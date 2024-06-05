from transformers import AutoTokenizer
import numpy as np
import evaluate
from torch.utils.data import DataLoader
import torch
from typing import Optional, List, Dict, Any, Tuple
import matplotlib.pyplot as plt
from tqdm import tqdm

metric = evaluate.load("seqeval")

def align_labels_with_tokens(labels: List[int], word_ids: List[Optional[int]]) -> List[int]:
    """
    Aligns labels with tokens.

    Args:
        labels (List[int]): Original labels.
        word_ids (List[Optional[int]]): Word IDs for each token.

    Returns:
        List[int]: Aligned labels.
    """
    new_labels = []
    current_word = None
    for word_id in word_ids:
        if word_id != current_word:
            current_word = word_id
            label = -100 if word_id is None else labels[word_id]
            new_labels.append(label)
        elif word_id is None:
            new_labels.append(-100)
        else:
            label = labels[word_id]
            if label % 2 == 1:
                label += 1
            new_labels.append(label)
    return new_labels

def tokenize_and_align_labels(examples: Dict[str, Any], 
                              tokenizer_name: str,
                              text_col: str, 
                              label_col: str,
                              embedding_type: str = "token", 
                              is_split_into_words:bool=True) -> Dict[str, Any]:
    """
    Tokenizes input text and aligns labels.

    Args:
        examples (Dict[str, Any]): Input examples containing 'tokens' and 'ner_tags'.
        tokenizer_name (str): Name of the tokenizer.

    Returns:
        Dict[str, Any]: Tokenized inputs with aligned labels.
    """
    if embedding_type == "token":
        tokenizer = AutoTokenizer.from_pretrained(tokenizer_name, add_prefix_space=True)
        tokenized_inputs = tokenizer(examples[text_col], truncation=True, is_split_into_words=is_split_into_words)
        all_labels = examples[label_col]
        new_labels = []
        for i, labels in enumerate(all_labels):
            word_ids = tokenized_inputs.word_ids(i)
            new_labels.append(align_labels_with_tokens(labels, word_ids))
        tokenized_inputs["labels"] = new_labels
    elif embedding_type == "sentence":
        tokenizer = AutoTokenizer.from_pretrained(tokenizer_name, add_prefix_space=True)
        tokenized_inputs = [[tokenizer(sentence, padding='max_length', truncation=True, return_tensors='pt') for sentence in sentence_list] for sentence_list in examples[text_col]]
        return {'tokenized_sentences': tokenized_inputs}
    else:
        raise ValueError("Unsupported embedding type.")
    return tokenized_inputs

def collate_fn(samples: List[Dict[str, Any]]) -> Dict[str, torch.Tensor]:
    """
    Collates samples into batches for the DataLoader.

    Args:
        samples (List[Dict[str, Any]]): List of samples.

    Returns:
        Dict[str, torch.Tensor]: Batch of input IDs, attention masks, and labels.
    """
    input_ids = [torch.tensor(sample['input_ids']) for sample in samples]
    attention_masks = [torch.tensor(sample['attention_mask']) for sample in samples]
    labels = [torch.tensor(sample['labels']) for sample in samples]

    input_ids = torch.nn.utils.rnn.pad_sequence(input_ids, batch_first=True, padding_value=0)
    attention_masks = torch.nn.utils.rnn.pad_sequence(attention_masks, batch_first=True, padding_value=0)
    labels = torch.nn.utils.rnn.pad_sequence(labels, batch_first=True, padding_value=-100)

    return {
        'input_ids': input_ids,
        'attention_mask': attention_masks,
        'labels': labels
    }

def evaluate_model(model: torch.nn.Module, 
             id2label: Dict[int, str], 
             dataloader: DataLoader, 
             use_crf: bool,
             device: str) -> Tuple[float, Dict[str, float]]:
    """
    Evaluates the model on the validation set.

    Args:
        model (torch.nn.Module): The model to evaluate.
        id2label (Dict[int, str]): Mapping from label IDs to label names.
        dataloader (DataLoader): DataLoader for the validation set.
        device (str): Device to perform evaluation on.

    Returns:
        float: Average validation loss.
        Dict[str, float]: Evaluation metrics.
    """
    model.eval()
    total_loss = 0.0
    with torch.no_grad():
        for batch in tqdm(dataloader, desc=f"Evaluation"):
            input_ids = batch['input_ids'].to(device)
            attention_mask = batch['attention_mask'].to(device)
            labels = batch['labels'].to(device)
            
            if use_crf:
                logits, loss, tags = model(input_ids, attention_mask, labels=labels)
                predictions =  [seq for seq in tags]
            else:
                logits, loss = model(input_ids, attention_mask, labels=labels)
                predictions = logits.argmax(dim=-1)
                predictions = predictions.detach().cpu().clone().numpy()
            total_loss += loss.item()
            
            labels = labels.detach().cpu().clone().numpy()

            true_labels = [[id2label[l] for l in label if l != -100] for label in labels]
            true_predictions = [
                [id2label[p] for (p, l) in zip(prediction, label) if l != -100]
                for prediction, label in zip(predictions, labels)
            ]

            metric.add_batch(predictions=true_predictions, references=true_labels)
    avg_loss = total_loss / len(dataloader)
    results = metric.compute()
    return avg_loss, results

def train_model(model: torch.nn.Module, 
                train_dataloader: DataLoader, 
                val_dataloader: DataLoader, 
                num_epochs: int,
                use_crf: bool,
                optimizer: Optional[torch.optim.Optimizer] = None,
                scheduler: Optional[torch.optim.lr_scheduler._LRScheduler] = None,
                clip_grad_norm: bool = False,
                patience: int = 3) -> None:
    """
    Trains the model with early stopping based on validation loss.

    Args:
        model (torch.nn.Module): The model to train.
        train_dataloader (DataLoader): DataLoader for the training set.
        val_dataloader (DataLoader): DataLoader for the validation set.
        num_epochs (int): Number of epochs to train for.
        optimizer (Optional[torch.optim.Optimizer]): Optimizer to use. Defaults to Adam.
        scheduler (Optional[torch.optim.lr_scheduler._LRScheduler]): Scheduler to use. Defaults to StepLR.
        clip_grad_norm (bool): Whether to clip gradients. Defaults to False.
        patience (int): Number of epochs to wait before early stopping. Defaults to 3.
    """
    if optimizer is None:
        optimizer = torch.optim.Adam([
            {'params': model.lstm.parameters(), 'lr': 1e-3},
            {'params': model.linear.parameters(), 'lr': 1e-3},
            {'params': model.crf.parameters(), 'lr': 1e-3}
            ])
    
    if scheduler is None:
        scheduler = torch.optim.lr_scheduler.StepLR(optimizer, step_size=3, gamma=0.1)
    device = "cuda" if torch.cuda.is_available() else "cpu"
    train_losses = []
    val_losses = []
    best_val_loss = float('inf')
    no_improvement_counter = 0
    for epoch in range(num_epochs):
        model.train()
        running_loss = 0.0
        for batch in tqdm(train_dataloader, desc=f"Training Epoch {epoch+1}"):
            input_ids = batch['input_ids'].to(device)
            attention_mask = batch['attention_mask'].to(device)
            labels = batch['labels'].to(device)

            optimizer.zero_grad()
            if use_crf:
                _, loss, _ = model(input_ids, attention_mask, labels=labels)
            else:
                _, loss = model(input_ids, attention_mask, labels=labels)
            loss.backward()
            if clip_grad_norm:
                torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)
            optimizer.step()

            running_loss += loss.item()

        avg_training_loss = running_loss / len(train_dataloader)
        val_loss, metrics = evaluate(model, model.labels, val_dataloader, use_crf, device)
        print(f'Epoch [{epoch + 1}/{num_epochs}]: Training Loss: {avg_training_loss:.4f}, Validation Loss: {val_loss:.4f}')
        print({key: metrics[f"overall_{key}"] for key in ["precision", "recall", "f1", "accuracy"]})

        train_losses.append(avg_training_loss)
        val_losses.append(val_loss)

        if val_loss < best_val_loss:
            best_val_loss = val_loss
            no_improvement_counter = 0
        else:
            no_improvement_counter += 1

        if no_improvement_counter >= patience:
            print(f'Validation loss has not improved for {patience} epochs. Early stopping...')
            break

        scheduler.step()

    print('Finished Training')

    # Plot the training and validation losses
    plt.plot(range(1, len(train_losses) + 1), train_losses, label='Training Loss')
    plt.plot(range(1, len(val_losses) + 1), val_losses, label='Validation Loss')
    plt.xlabel('Epoch')
    plt.ylabel('Loss')
    plt.title('Training and Validation Loss')
    plt.legend()
    plt.show()

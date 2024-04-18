def generate_annotations(entities):
    annotations = []  # List to store annotations

    # Iterate through the entities list
    for entity in entities:
        # Check if the entity has bbox_span attribute
        if hasattr(entity, 'bbox_span') and entity.bbox_span:
            for bbox_list in entity.bbox_span:
                if bbox_list != None:
                # if 'page' in bbox_list and bbox_list != None:                            
                    annotation = {
                        "page": bbox_list["page"],
                        "x": bbox_list.get("left", 0),  # Use default value if 'left' key is missing
                        "y": bbox_list.get("top", 0),   # Use default value if 'top' key is missing
                        "height": bbox_list.get("height", 0),  # Use default value if 'height' key is missing
                        "width": bbox_list.get("width", 0),    # Use default value if 'width' key is missing
                        "color": "red"  # Adjust color as needed
                    }
                    annotations.append(annotation)

    return annotations

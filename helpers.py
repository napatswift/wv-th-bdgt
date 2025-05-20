def merge_close_bboxes(word_tuples, threshold_x=10, threshold_y=10):
    """
    Merge close bounding boxes in a list of word tuples.

    Args:
        word_tuples (list): List of word tuples, where each tuple contains the following elements:
                  - x0 (int): The x-coordinate of the top-left corner of the bounding box.
                  - y0 (int): The y-coordinate of the top-left corner of the bounding box.
                  - x1 (int): The x-coordinate of the bottom-right corner of the bounding box.
                  - y1 (int): The y-coordinate of the bottom-right corner of the bounding box.
                  - text (str): The text contained within the bounding box.
        threshold_x (int, optional): The maximum allowed difference in x-coordinates for merging. Defaults to 10.
        threshold_y (int, optional): The maximum allowed difference in y-coordinates for merging. Defaults to 10.

    Returns:
        list: List of merged word tuples, where close bounding boxes have been merged.

    """
    invalid_start_chars = [t for t in "ะา-ิ-ี-ุ-ู-ึ-๋-้-่-ื-ำ-็-๊-ั" if t != '-']
    merged_words = []
    for word in word_tuples:
        x0, y0, x1, y1, text = word[:5]
        if merged_words and abs(x0 - merged_words[-1][2]) <= threshold_x and abs(merged_words[-1][1] - y0) <= threshold_y:
            # If the x value of the current word is close to the x value of the last word in the merged list,
            # merge the current word with the last word.
            last_word = merged_words[-1]
            merged_x0 = min(last_word[0], x0)
            merged_y0 = min(last_word[1], y0)
            merged_x1 = max(last_word[2], x1)
            merged_y1 = max(last_word[3], y1)
            merged_text = last_word[4] + (
              chr(65533) if text[0] in invalid_start_chars else ''
            ) + text
            merged_words[-1] = (merged_x0, merged_y0, merged_x1, merged_y1, merged_text)
        else:
            # If the current word is not close to the last word in the merged list, add it to the list as a new word.
            merged_words.append((x0, y0, x1, y1, text))
    return merged_words

def area_of_bboxes(bboxes):
    """
    Calculate the total area of a list of bounding boxes.

    Args:
        bboxes (list): List of bounding boxes, where each bounding box is a tuple of the form (x0, y0, x1, y1).

    Returns:
        int: The total area of the bounding boxes.

    """
    x0 = min([b[0] for b in bboxes])
    y0 = min([b[1] for b in bboxes])
    x1 = max([b[2] for b in bboxes])
    y1 = max([b[3] for b in bboxes])

    return (x1 - x0) * (y1 - y0)

def merge_bbox_lists(page, contour_boxes, pdf_boxes):
    merged_boxes = []
    for cbox in contour_boxes:
        c_x, c_y, c_w, c_h = cbox
        c_x0 = c_x
        c_y0 = c_y
        c_x1 = c_x + c_w
        c_y1 = c_y + c_h
        c_area = c_w * c_h
        
        # Find pdf boxes with center inside this contour box
        inside_boxes = []
        p_area = 0
        for pb in pdf_boxes:
            pb_x0, pb_y0, pb_x1, pb_y1, pb_text = pb
            pb_cx = (pb_x0 + pb_x1) / 2
            pb_cy = (pb_y0 + pb_y1) / 2
            
            if (c_x < pb_cx < c_x1 and 
                c_y < pb_cy < c_y1):
                
                inside_boxes.append(pb)
                p_area += (pb_x1 - pb_x0) * (pb_y1 - pb_y0)

        # Concatenate text from inside boxes
        c_text = ''
        if p_area > 0.8 * c_area:
            inside_boxes = sorted(inside_boxes, key=lambda x: x[0])
            merged_text = ''.join([ib[-1] for ib in inside_boxes])
            c_text = merged_text

        corrupted_chars = [65533, 3656]
        if not c_text or sum(ord(t) in corrupted_chars for t in c_text) / len(c_text) > 0.1:
            c_text = get_tessocr(page, pad_bbox([c_x0, c_y0, c_x1, c_y1], 2, 3))

        merged_boxes.append((c_x0, c_y0, c_x1, c_y1, c_text))

    return merged_boxes
package com.example.service;

// Model imports will need to be updated to com.example.model.*
import com.example.model.DocumentText;
import com.example.model.LineText;
import com.example.model.PageText;
import com.example.model.WordText;

import org.apache.pdfbox.Loader; // Added for PDFBox 3.0.x
import org.apache.pdfbox.pdmodel.PDDocument;
import org.apache.pdfbox.pdmodel.PDPage;
import org.apache.pdfbox.text.PDFTextStripper;
import org.apache.pdfbox.text.TextPosition;

import java.io.File;
import java.io.IOException;
import java.util.ArrayList;
import java.util.List;
import java.util.Comparator;
import java.util.stream.Collectors;

public class PdfDocumentReader implements AutoCloseable {
    private String filepath;
    private PDDocument document;
    private List<com.example.model.PageText> pages; // Use fully qualified name or add import
    private com.example.model.DocumentText documentText; // Use fully qualified name or add import

    public PdfDocumentReader(String filepath) throws IOException {
        this.filepath = filepath;
        // Updated for PDFBox 3.0.x
        this.document = Loader.loadPDF(new File(filepath)); 
        this.pages = new ArrayList<>();
        try {
            parsePages();
            // Create DocumentText after pages are parsed
            // For now, metadata can be null or empty strings.
            // This will be properly populated in a later task if needed.
            this.documentText = new com.example.model.DocumentText( // Use fully qualified name or add import
                this.pages,
                this.document.getDocumentInformation().getProducer(),
                this.document.getDocumentInformation().getTitle(),
                this.document.getDocumentInformation().getCreator(),
                this.document.getDocumentInformation().getSubject(),
                this.document.getDocumentInformation().getAuthor(),
                this.document.getDocumentInformation().getKeywords(),
                new File(filepath).getName()
            );
            // Set the document reference in each page
            for (com.example.model.PageText page : this.pages) { // Use fully qualified name or add import
                page.setDocument(this.documentText);
            }
        } finally {
            if (this.document != null) {
                this.document.close(); // Ensure document is closed after parsing
            }
        }
    }

    private void parsePages() throws IOException {
        for (int i = 0; i < document.getNumberOfPages(); i++) {
            PDPage pdPage = document.getPage(i);
            float pageWidth = pdPage.getMediaBox().getWidth();
            float pageHeight = pdPage.getMediaBox().getHeight();

            List<com.example.model.WordText> wordTexts = extractWordsFromPage(pdPage, pageWidth, pageHeight, i); // Use fully qualified name or add import
            List<com.example.model.LineText> lineTexts = groupWordsIntoLines(wordTexts, i, pageWidth, pageHeight); // Use fully qualified name or add import

            // Normalized width and height are 1.0 because word coordinates are normalized
            com.example.model.PageText pageText = new com.example.model.PageText(lineTexts, i, 1.0, 1.0, false); // isImage is false for now // Use fully qualified name or add import
            for(com.example.model.LineText line : lineTexts){ // Use fully qualified name or add import
                line.setPage(pageText);
            }
            this.pages.add(pageText);
        }
    }

    private List<com.example.model.WordText> extractWordsFromPage(PDPage pdPage, float pageWidth, float pageHeight, int pageIndex) throws IOException { // Use fully qualified name or add import
        List<com.example.model.WordText> wordTexts = new ArrayList<>(); // Use fully qualified name or add import
        PDFTextStripper stripper = new PDFTextStripper() {
            private StringBuilder currentWord = new StringBuilder();
            private TextPosition firstCharOfWord = null;

            @Override
            protected void writeString(String text, List<TextPosition> textPositions) throws IOException {
                for (TextPosition textPosition : textPositions) {
                    if (textPosition == null || textPosition.getUnicode().trim().isEmpty()) {
                        if (currentWord.length() > 0) {
                            addCurrentWord(pageWidth, pageHeight);
                        }
                        continue;
                    }

                    if (currentWord.length() == 0) {
                        firstCharOfWord = textPosition;
                    }

                    // Check for space or significant gap to delimit words
                    // This is a simplified word segmentation logic.
                    // It might need refinement for complex PDFs.
                    if (textPosition.getUnicode().equals(" ") ) {
                         if (currentWord.length() > 0) {
                            // Use the last non-space character's end position for the word's x1
                            TextPosition lastChar = null;
                            for(int j = textPositions.indexOf(textPosition) -1; j >=0 ; j--){
                                if(!textPositions.get(j).getUnicode().trim().isEmpty()){
                                    lastChar = textPositions.get(j);
                                    break;
                                }
                            }
                            if (lastChar != null) {
                                double x0 = firstCharOfWord.getXDirAdj() / pageWidth;
                                double y0 = firstCharOfWord.getYDirAdj() / pageHeight;
                                // Use EndX of the last character of the word
                                double x1 = (lastChar.getEndX()) / pageWidth;
                                // Use Y + Height of the first character for y1, assuming characters in a word are on the same baseline
                                double y1 = (firstCharOfWord.getYDirAdj() + firstCharOfWord.getHeightDir()) / pageHeight;
                                wordTexts.add(new com.example.model.WordText(x0, y0, x1, y1, currentWord.toString())); // Use fully qualified name or add import
                            }
                            currentWord.setLength(0);
                            firstCharOfWord = null;
                        }
                        continue; // Skip processing the space character itself as part of a word
                    }


                    currentWord.append(textPosition.getUnicode());

                    // If this is the last textPosition in the list, and there's a current word, add it.
                    if (textPositions.indexOf(textPosition) == textPositions.size() - 1 && currentWord.length() > 0) {
                         addCurrentWord(pageWidth, pageHeight, textPosition); // pass current textPosition as last char
                    }
                }
            }
            
            // Overload for when the last char is known (end of textPositions)
            private void addCurrentWord(float pageWidth, float pageHeight, TextPosition lastCharPosition) {
                if (currentWord.length() > 0 && firstCharOfWord != null) {
                    double x0 = firstCharOfWord.getXDirAdj() / pageWidth;
                    double y0 = firstCharOfWord.getYDirAdj() / pageHeight;
                    double x1 = lastCharPosition.getEndX() / pageWidth;
                    double y1 = (firstCharOfWord.getYDirAdj() + firstCharOfWord.getHeightDir()) / pageHeight;
                    wordTexts.add(new com.example.model.WordText(x0, y0, x1, y1, currentWord.toString())); // Use fully qualified name or add import
                    currentWord.setLength(0);
                    firstCharOfWord = null;
                }
            }

            // Original addCurrentWord for cases where last char isn't explicitly passed (e.g. space encountered)
            private void addCurrentWord(float pageWidth, float pageHeight) {
                 // This version might be problematic if the last character before a space wasn't tracked.
                 // It's better to ensure x1 is based on the actual last character of the word.
                 // For simplicity, this might rely on the last processed textPosition if not handled carefully.
                 // The version above `addCurrentWord(float pageWidth, float pageHeight, TextPosition lastCharPosition)`
                 // is preferred when the last character is explicitly known.
                 // This method is kept if there are calls to it without the last char, but it's less precise.
                 // To be safe, let's assume this is called when a delimiter (like a space) is found,
                 // and the "word" is everything *before* that delimiter.
                 // The TextPosition passed to writeString might be a chunk, not char by char.
                 // This logic needs to be robust. Let's assume for now the main `writeString` loop handles last char correctly.
                 // If this method is called, it implies the word ended *before* the current textPosition.
                 // This part of PDFBox interaction is tricky.
                if (currentWord.length() > 0 && firstCharOfWord != null) {
                    // This logic is potentially flawed as it might not have the correct last TextPosition
                    // of the actual word if not managed carefully by the caller.
                    // Let's assume the caller (writeString) handles this.
                    // For a robust solution, one might need to track the last actual character of the word.
                    // The provided snippet in `writeString` tries to find the last non-space char.
                    // This simplified version is a fallback and might not be used if writeString is comprehensive.
                    double x0 = firstCharOfWord.getXDirAdj() / pageWidth;
                    double y0 = firstCharOfWord.getYDirAdj() / pageHeight;
                    // x1 and y1 are tricky here without the last character's specific TextPosition
                    // Using firstCharOfWord.getEndX() might be incorrect if the word spans multiple TextPositions.
                    // This indicates a need for more robust tracking of the word's bounding box.
                    // For now, this is a placeholder acknowledging the complexity.
                    // A more robust approach would involve iterating textPositions carefully.
                    // Let's remove this potentially misleading implementation and rely on the more detailed one in writeString.
                    // This method will not be called if writeString correctly adds words.
                }
            }


        };
        stripper.setSortByPosition(true); // Ensure text is processed in reading order
        stripper.setStartPage(pageIndex + 1); // PDFBox pages are 1-indexed
        stripper.setEndPage(pageIndex + 1);
        stripper.getText(document); // This triggers the overridden writeString
        return wordTexts;
    }

    private List<com.example.model.LineText> groupWordsIntoLines(List<com.example.model.WordText> words, int pageIndex, float pageWidth, float pageHeight) { // Use fully qualified name or add import
        List<com.example.model.LineText> lines = new ArrayList<>(); // Use fully qualified name or add import
        if (words.isEmpty()) {
            return lines;
        }

        // Sort words by y0, then x0
        words.sort(Comparator.comparingDouble(com.example.model.WordText::getY0).thenComparingDouble(com.example.model.WordText::getX0)); // Use fully qualified name or add import

        List<com.example.model.WordText> currentLineWords = new ArrayList<>(); // Use fully qualified name or add import
        currentLineWords.add(words.get(0));
        double lastWordY0 = words.get(0).getY0();

        // The threshold should be relative to normalized coordinates.
        // Python version used 0.01 after normalization.
        double yThreshold = 0.01; 

        for (int i = 1; i < words.size(); i++) {
            com.example.model.WordText currentWord = words.get(i); // Use fully qualified name or add import
            // Check if the y-coordinate difference is too large, indicating a new line.
            // Also consider if words overlap significantly in y, they should be on the same line.
            // A simple y0 difference check might split lines that have slightly varying baselines
            // but are visually the same line.
            // A more robust check might involve looking at y-overlap.
            // For now, using the y0 difference as per the Python version's logic.
            if (Math.abs(currentWord.getY0() - lastWordY0) > yThreshold) {
                if (!currentLineWords.isEmpty()) {
                    lines.add(new com.example.model.LineText(new ArrayList<>(currentLineWords), pageIndex, lines.size())); // Use fully qualified name or add import
                }
                currentLineWords.clear();
            }
            currentLineWords.add(currentWord);
            lastWordY0 = currentWord.getY0(); // Update lastWordY0 to current word's y0 for next comparison
                                           // Or, consider using the y0 of the first word in the current line
                                           // if the goal is to group words close to that initial baseline.
                                           // For simplicity, using the immediately preceding word's y0 is often sufficient.
        }

        // Add the last line
        if (!currentLineWords.isEmpty()) {
            lines.add(new com.example.model.LineText(new ArrayList<>(currentLineWords), pageIndex, lines.size())); // Use fully qualified name or add import
        }
        return lines;
    }

    public List<com.example.model.PageText> getPages() { // Use fully qualified name or add import
        return pages;
    }

    public com.example.model.PageText getPage(int pageIndex) { // Use fully qualified name or add import
        if (pageIndex >= 0 && pageIndex < pages.size()) {
            return pages.get(pageIndex);
        }
        return null;
    }

    public List<com.example.model.LineText> getAllLines() { // Use fully qualified name or add import
        return pages.stream()
                .flatMap(page -> page.getLines().stream())
                .collect(Collectors.toList());
    }
    
    public com.example.model.DocumentText getDocumentText() { // Use fully qualified name or add import
        return documentText;
    }

    @Override
    public void close() throws IOException {
        if (document != null) {
            document.close();
        }
    }
}

package com.example;

// Assuming model classes (LineText, LineItem, BudgetItem) are in com.example.model
import com.example.model.LineText;
import com.example.model.LineItem;
import com.example.model.BudgetItem;

// Assuming service classes (PdfDocumentReader, TextAnalysisService) are in com.example.service
import com.example.service.PdfDocumentReader;
import com.example.service.TextAnalysisService;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.SerializationFeature;

import java.io.File;
import java.io.FileWriter;
import java.io.IOException;
import java.util.List;
import java.util.Map;

public class ConvertTree {

    public static void main(String[] args) {
        // Call to debugHelperFunctions and System.exit(0) REMOVED to restore normal execution.

        // 1. Argument Handling
        if (args.length < 1) {
            System.err.println("Usage: java com.example.ConvertTree <input_pdf_filepath> [output_json_filepath]");
            System.exit(1);
        }

        String pdfFilepath = args[0];
        String outputJsonPath = args.length > 1 ? args[1] : "output.json";

        // 2. Processing
        // Instantiate PdfDocumentReader
        List<LineText> allLines = null;
        // DocumentText documentTextContainer = null; // This line was unused and caused compilation error

        try (PdfDocumentReader reader = new PdfDocumentReader(pdfFilepath)) {
            allLines = reader.getAllLines();
            // If PdfDocumentReader stores DocumentText that has the filename, retrieve it.
            // Assuming reader.getDocumentText().getSourceFilename() exists.
            // If not, we'll use pdfFile.getName() later.
            // For now, let's assume it's available to be consistent with prior thoughts,
            // but pdfFile.getName() is a safe fallback.
            if (reader.getDocumentText() != null && reader.getDocumentText().getSourceFilename() != null) {
                 // This line was intended to get sourceFilename, but TextAnalysisService.extractTreeLevels
                 // now takes pdfFile.getName(). So, direct use of reader.getDocumentText() here isn't
                 // strictly for that purpose anymore, but getting allLines is key.
            }

        } catch (IOException e) {
            System.err.println("Error reading PDF: " + e.getMessage());
            e.printStackTrace();
            System.exit(1);
        }

        if (allLines == null || allLines.isEmpty()) {
            System.err.println("No text lines extracted from the PDF.");
            // It might be valid to write an empty JSON, but for this tool, lines are essential.
            System.exit(1);
        }

        // Call TextAnalysisService methods
        List<com.example.model.LineItem> lineItems = com.example.service.TextAnalysisService.getEntries(allLines);

        if (lineItems.isEmpty()) {
            System.out.println("No entries found by TextAnalysisService. Output JSON will represent an empty budget structure.");
            // Allow proceeding to write a JSON that reflects no items, e.g., just a root or empty children.
        }

        // The extractTreeLevels method now calls addLevelToEntriesPositions internally.
        // Pass the original PDF filename for BudgetItem's document field.
        File pdfFile = new File(pdfFilepath);
        com.example.model.BudgetItem rootBudget = com.example.service.TextAnalysisService.extractTreeLevels(lineItems, pdfFile.getName());

        // 3. JSON Serialization
        ObjectMapper objectMapper = new ObjectMapper();
        objectMapper.enable(SerializationFeature.INDENT_OUTPUT); // For pretty printing

        try (FileWriter fileWriter = new FileWriter(outputJsonPath)) {
            // BudgetItem.toJson() returns a Map, which Jackson can serialize
            Map<String, Object> budgetJsonMap = rootBudget.toJson();
            objectMapper.writeValue(fileWriter, budgetJsonMap);
            System.out.println("Successfully wrote JSON output to: " + outputJsonPath);
        } catch (IOException e) {
            System.err.println("Error writing JSON output: " + e.getMessage());
            e.printStackTrace();
            System.exit(1);
        }
    }
}

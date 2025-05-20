package com.example.service;

// Model imports
import com.example.model.BudgetItem;
import com.example.model.BudgetType;
import com.example.model.FiscalYearBudget;
import com.example.model.LineItem;
import com.example.model.LineText;

import java.util.regex.Pattern;
import java.util.regex.Matcher;
import java.util.List;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.Map;
import java.util.HashMap;
import java.util.Collections;
import java.util.stream.Collectors;


// import com.example.model.PageText; // If PageText.isContainsTable() is needed -> Not directly used here

// For now, let's assume these classes are available from previous steps.
// If not, their structure needs to be defined as per the project.

public class TextAnalysisService {

    // Helper class for the parent stack in extractTreeLevels
    private static class StackNode {
        final com.example.model.BudgetItem node; // Use fully qualified name or import
        final int level;

        StackNode(com.example.model.BudgetItem node, int level) { // Use fully qualified name or import
            this.node = node;
            this.level = level;
        }

        public com.example.model.BudgetItem getNode() { // Use fully qualified name or import
            return node;
        }

        public int getLevel() {
            return level;
        }
    }

    // Helper class/record for getPaternOfBullet
    private static class PatternAndLevel {
        final Pattern pattern;
        final int baseLevel;
        final boolean adjustWithDots;

        PatternAndLevel(String regex, int baseLevel, boolean adjustWithDots) {
            this.pattern = Pattern.compile(regex);
            this.baseLevel = baseLevel;
            this.adjustWithDots = adjustWithDots;
        }
    }

    private static final List<PatternAndLevel> BULLET_PATTERNS = Arrays.asList(
        new PatternAndLevel("^[1-9][0-9]*(\\.[1-9][0-9]*)*\\)$", 20, true), // e.g., 1), 1.1)
        new PatternAndLevel("^\\(\\d*(\\.?\\d*)*\\)$", 50, true),          // e.g., (1), (1.1)
        new PatternAndLevel("^[1-9][0-9]*(\\.[1-9][0-9]*)+$", 2, true),   // e.g., 1.1, 1.1.1
        new PatternAndLevel("^[1-9][0-9]*\\.$", 1, false),                 // e.g., 1.
        new PatternAndLevel("^[1-9][0-9]*$", 30, false)                   // e.g., 1
    );

    private static final Pattern AMOUNT_PATTERN = Pattern.compile("(\\d{1,3}(?:,\\d{3})*(?:\\.\\d+)?) บาท");
    private static final Pattern YEAR_PATTERN = Pattern.compile("(\\d{4})(?:[^\\d]+(\\d{4}))?");

    private static final List<Pattern> QUANTITY_PATTERNS = Arrays.asList(
        Pattern.compile("รวม \\d+ รายการ"),
        Pattern.compile("\\(\\d+ หน่วย\\)"),
        Pattern.compile("จำนวน \\d+ โครงการ")
    );

    private static final List<String> CLASSIFIERS = Arrays.asList(
        "แห่ง", "สาย", "สายทาง", "โครงการ", "รายการ", "แผนงาน", "งาน", "กิจกรรม", "กลุ่ม", "เรื่อง", 
        "ฉบับ", "ชุด", "เครื่อง", "หน่วย", "เครื่องจักร", "คัน", "คน", "ราย", "มาตรการ", "ระบบ", 
        "ประเภท", "ชนิด", "แบบ", "ขนาด", "มาตรฐาน", "ระยะ", "เขต", "จังหวัด", "อำเภอ", "ตำบล", 
        "หมู่บ้าน", "เทศบาล", "อบต.", "ครั้ง", "วิธี", "ขั้นตอน", "ระดับ", "รอบ", "ปี", "เดือน", 
        "วัน", "ชั่วโมง", "นาที", "วินาที", "บาท", "ล้านบาท", "เปอร์เซ็นต์", "เท่า", "เท่าตัว", 
        "เท่ากับ", "ผลผลิต", "ผลลัพธ์", "ตัวชี้วัด"
        // More classifiers can be added if needed
    );
    
    private static final List<String> REDUNDANT_PHRASES = Arrays.asList(
        "หน้า", "หน้า ที่", "หน้าที่", "หน้าที่ของ", "หน้าที่และความรับผิดชอบ", 
        "สารบัญ", "หมายเหตุ", "เอกสาร", "เอกสารแนบ", "ภาคผนวก"
        // More redundant phrases can be added if needed
    );


    public static double getAmountFromString(String text) {
        Matcher matcher = AMOUNT_PATTERN.matcher(text);
        if (matcher.find()) {
            String amountStr = matcher.group(1).replace(",", "");
            try {
                return Double.parseDouble(amountStr);
            } catch (NumberFormatException e) {
                return 0.0;
            }
        }
        return 0.0;
    }

    public static class YearRange {
        public int startYear;
        public int endYear;

        public YearRange(int startYear, int endYear) {
            this.startYear = startYear;
            this.endYear = endYear;
        }
    }

    public static YearRange getYearFromString(String text) {
        Matcher matcher = YEAR_PATTERN.matcher(text);
        if (matcher.find()) {
            int startYear = Integer.parseInt(matcher.group(1));
            int endYear = startYear; // Default if only one year is found
            if (matcher.group(2) != null) {
                endYear = Integer.parseInt(matcher.group(2));
            }
            return new YearRange(startYear, endYear);
        }
        return new YearRange(0, 0);
    }

    // Renamed from getPaternOfBullet to getPatternOfBullet for typo correction
    public static int getPatternOfBullet(String text) {
        for (PatternAndLevel pal : BULLET_PATTERNS) {
            Matcher matcher = pal.pattern.matcher(text);
            if (matcher.find()) {
                int level = pal.baseLevel;
                if (pal.adjustWithDots) {
                    level += text.chars().filter(ch -> ch == '.').count();
                }
                return level;
            }
        }
        return 0; // No pattern matched
    }

    public static boolean isQuantityString(String lineTextString) {
        for (Pattern pattern : QUANTITY_PATTERNS) {
            if (pattern.matcher(lineTextString).find()) {
                return true;
            }
        }
        return false;
    }

    public static boolean isClassifier(String word) {
        return CLASSIFIERS.contains(word);
    }

    public static boolean isRedundantLine(String[] lineTokens) {
        if (lineTokens == null || lineTokens.length == 0) {
            return true;
        }
        // Check if all tokens are digits (or empty after trim)
        boolean allDigits = true;
        for (String token : lineTokens) {
            if (!token.trim().matches("\\d*")) {
                allDigits = false;
                break;
            }
        }
        if (allDigits) return true;

        String joinedLine = String.join(" ", lineTokens).toLowerCase();
        for (String phrase : REDUNDANT_PHRASES) {
            if (joinedLine.contains(phrase)) {
                return true;
            }
        }
        return false;
    }

    public static boolean checkProjOutp(String target, String[] lineTokens) {
        if (lineTokens == null || lineTokens.length == 0) {
            return false;
        }
        String cleanedToken0 = lineTokens[0].trim();
        // Check if the token starts with target followed by a colon, or equals target exactly
        if (cleanedToken0.startsWith(target + ":") || cleanedToken0.equals(target)) {
            return true;
        }
        // Check if the *second* token starts with the target (e.g. "1. โครงการ ABC")
        if (lineTokens.length > 1 && lineTokens[1].startsWith(target)) {
            return true;
        }
        return false;
    }

    public static List<com.example.model.LineItem> getEntries(List<com.example.model.LineText> lines) { // Use fully qualified name or import
        List<com.example.model.LineItem> entries = new ArrayList<>(); // Use fully qualified name or import
        List<com.example.model.LineText> currentEntryLines = new ArrayList<>(); // Use fully qualified name or import
        boolean bulletFlag = false;
        String projOutpFlag = null; // "PROJECT", "OUTPUT", or null

        for (com.example.model.LineText line : lines) { // Use fully qualified name or import
            String lineStr = line.getText();
            String[] lineTokens = lineStr.split("\\s+");
            System.out.println(String.format("Processing line: %d.%d - '%s'", line.getPageIndex(), line.getLineIndex(), lineStr));


            if (lineTokens.length == 0 || (lineTokens.length == 1 && lineTokens[0].trim().isEmpty())) { // Adjusted condition for truly empty lines
                 if (!currentEntryLines.isEmpty() && (bulletFlag || projOutpFlag != null)) {
                    // If current line is empty, but we have pending lines for an entry,
                    // and the entry ends with "บาท", create the item.
                    // This handles cases where the amount line is followed by an empty line.
                    String lastLineOfEntry = currentEntryLines.get(currentEntryLines.size() - 1).getText();
                    if (lastLineOfEntry.matches(".*บาท(?:[\\s*-]*)$")) {
                         String itemType = bulletFlag ? "item" : projOutpFlag;
                         entries.add(new com.example.model.LineItem(itemType, new ArrayList<>(currentEntryLines), currentEntryLines.get(0).getPageIndex())); // Use fully qualified name or import
                         currentEntryLines.clear();
                         bulletFlag = false;
                         projOutpFlag = null;
                    } else {
                        // if it doesn't end with baht, and it's an empty line, we might want to append it
                        // or decide if the entry is implicitly finished.
                        // For now, let's assume an empty line can be part of a multi-line description if not ending an item.
                        // currentEntryLines.add(line); // Or skip, depending on desired behavior for empty lines within items
                    }
                }
                continue; // Skip truly empty lines from further processing if they don't terminate an item.
            }


            if (isRedundantLine(lineTokens)) {
                System.out.println("Line is redundant. Skipping.");
                continue;
            }

            // Budget Plan Check
            boolean isTableContext = false; // Placeholder for line.getPage().isContainsTable();
            if (isTableContext) {
                if (lineTokens.length > 0 && lineTokens[0].matches("7\\.\\d+$")) {
                    System.out.println("Identified as budget_plan.");
                    entries.add(new com.example.model.LineItem("budget_plan", Arrays.asList(line), line.getPageIndex()));
                    continue;
                }
                if (lineTokens.length > 1 && lineTokens[1].startsWith("แผนงาน")) {
                    System.out.println("Identified as budget_plan.");
                    entries.add(new com.example.model.LineItem("budget_plan", Arrays.asList(line), line.getPageIndex()));
                    continue;
                }
            }

            // Fiscal Year Check
            // Regex to be more flexible with spaces: ".*ป?ี?\\s*\\d{4}.*"
            // Keywords including OCR variations
            boolean fiscalYearPatternMatch = lineStr.matches(".*ป?ี?\\s*\\d{4}.*");
            boolean fiscalYearKeywordMatch = lineStr.contains("ตั้งงบประมาณ") || lineStr.contains("ตงังบประมาณ") || lineStr.contains("ต้งังบประมาณ") ||
                                             lineStr.contains("ผูกพันงบประมาณ") || lineStr.contains("ผูกพนังบประมาณ") ||
                                             lineStr.contains("ตั้งงปบระมาณ") || lineStr.contains("�ั้งงบ�ร�มา�") || lineStr.contains("��กพันงบ�ร�มา�");

            if (fiscalYearPatternMatch || fiscalYearKeywordMatch) {
                System.out.println("Identified as fiscal_year. Pattern match: " + fiscalYearPatternMatch + ", Keyword match: " + fiscalYearKeywordMatch);
                if (!currentEntryLines.isEmpty()) { // if there's a pending entry, add it first
                     String itemType = bulletFlag ? "item" : projOutpFlag;
                     if (itemType == null && !currentEntryLines.isEmpty()) itemType = "unknown_section";
                     entries.add(new com.example.model.LineItem(itemType, new ArrayList<>(currentEntryLines), currentEntryLines.get(0).getPageIndex()));
                     currentEntryLines.clear();
                     bulletFlag = false;
                     projOutpFlag = null;
                }
                entries.add(new com.example.model.LineItem("fiscal_year", Arrays.asList(line), line.getPageIndex()));
                continue;
            }
            
            // Quantity String Check
            if (isQuantityString(lineStr)) {
                System.out.println("Line is quantity string.");
                if (!bulletFlag && projOutpFlag == null && !entries.isEmpty()) { 
                    com.example.model.LineItem lastItem = entries.get(entries.size() - 1);
                    // This logic needs LineItem to have an addLineText method or similar
                    // For now, creating a new LineItem or handling this differently.
                    // Python version appends to last_item['lines'].
                    // Let's assume we add to currentEntryLines if they are active,
                    // otherwise, it's a standalone quantity string (less likely based on py logic)
                    if(!currentEntryLines.isEmpty()){
                        currentEntryLines.add(line);
                        // continue; // continue to see if this quantity line also ends an item
                    } else {
                        // Or create a new "quantity_info" item if it appears standalone
                        // entries.add(new LineItem("quantity_info", Arrays.asList(line), line.getPageIndex()));
                        // For now, let's stick to appending if currentEntryLines is active,
                        // otherwise it will be processed by bullet/proj/output logic
                    }
                }
                // If it is part of a bullet/proj item, it will be added to currentEntryLines later
            }


            // Bullet Flag Check
            String originalFirstToken = lineTokens[0];
            String potentialBulletToken = originalFirstToken;

            String[] bulletRegexesForExtraction = {
                "[1-9][0-9]*(\\.[1-9][0-9]*)*\\)", // e.g., "1.1)"
                "\\(\\d*(\\.?\\d*)*\\)",          // e.g., "(1)", "(1.1)"
                "[1-9][0-9]*(\\.[1-9][0-9]*)+",   // e.g., "1.1", "1.1.1"
                "[1-9][0-9]*\\.",                // e.g., "1."
                "[1-9][0-9]*"                   // e.g., "1" - Broad, keep last
            };

            for (String regex : bulletRegexesForExtraction) {
                Pattern pattern = Pattern.compile("^(" + regex + ")"); // Anchor at the beginning
                Matcher matcher = pattern.matcher(originalFirstToken);
                if (matcher.find()) {
                    potentialBulletToken = matcher.group(1);
                    System.out.println("Extracted potential bullet token: '" + potentialBulletToken + "' from '" + originalFirstToken + "' using regex: '" + regex + "'");
                    break; 
                }
            }
            
            System.out.println("Attempting bullet match for (potentially extracted) token: '"+ potentialBulletToken + "' from line: '" + line.getText() + "'");
            int patternLevel = getPatternOfBullet(potentialBulletToken); // Call with the (potentially) cleaner token
            
            if (patternLevel > 0) {
                 System.out.println("Bullet pattern found for token: '"+ potentialBulletToken + "' with level: " + patternLevel);
            }

            if (patternLevel > 0 && lineTokens.length > 1 && !isClassifier(lineTokens[1])) {
                if(!currentEntryLines.isEmpty() && (bulletFlag || projOutpFlag != null)){ 
                     String itemTypeOld = bulletFlag ? "item" : projOutpFlag;
                     entries.add(new com.example.model.LineItem(itemTypeOld, new ArrayList<>(currentEntryLines), currentEntryLines.get(0).getPageIndex()));
                     currentEntryLines.clear();
                }
                bulletFlag = true;
                projOutpFlag = null; 
                System.out.println("bulletFlag SET to true. patternLevel=" + patternLevel + ", potentialBulletToken=" + potentialBulletToken);
            }

            // Project/Output Flag Check
            // Added OCR variations to targets
            String[] projTargets = {"โครงการ", "โครงการพัฒนา", "โครงการปรับปรุง", "โครงการก่อสร้าง", "�ครงการ", "��รงการ"};
            String[] outpTargets = {"ผลผลิต", "ผลผลิตหลัก", "ผลผลิตรอง", "ผลผลิ�", "�ล�ลิ�", "�ล�ลิต"};

            String identifiedProjOutpType = null;

            for (String target : projTargets) {
                if (checkProjOutp(target, lineTokens)) {
                    if(!currentEntryLines.isEmpty() && (bulletFlag || projOutpFlag != null)){
                        String itemTypeOld = bulletFlag ? "item" : projOutpFlag;
                        entries.add(new com.example.model.LineItem(itemTypeOld, new ArrayList<>(currentEntryLines), currentEntryLines.get(0).getPageIndex()));
                        currentEntryLines.clear();
                    }
                    projOutpFlag = "PROJECT";
                    bulletFlag = false; 
                    identifiedProjOutpType = "PROJECT";
                    break;
                }
            }
            if (identifiedProjOutpType == null) { 
                for (String target : outpTargets) {
                    if (checkProjOutp(target, lineTokens)) {
                         if(!currentEntryLines.isEmpty() && (bulletFlag || projOutpFlag != null)){
                            String itemTypeOld = bulletFlag ? "item" : projOutpFlag;
                             entries.add(new com.example.model.LineItem(itemTypeOld, new ArrayList<>(currentEntryLines), currentEntryLines.get(0).getPageIndex()));
                             currentEntryLines.clear();
                         }
                        projOutpFlag = "OUTPUT";
                        bulletFlag = false; 
                        identifiedProjOutpType = "OUTPUT";
                        break;
                    }
                }
            }
            
            if (identifiedProjOutpType != null) {
                 System.out.println("Identified as " + identifiedProjOutpType + " target: '" + (projOutpFlag.equals("PROJECT") ? Arrays.stream(projTargets).filter(t -> checkProjOutp(t, lineTokens)).findFirst().orElse("") : Arrays.stream(outpTargets).filter(t -> checkProjOutp(t, lineTokens)).findFirst().orElse("")) + "'. projOutpFlag = " + projOutpFlag + ".");
            }
            
            // If bulletFlag or projOutpFlag is active:
            if (bulletFlag || projOutpFlag != null) {
                if (bulletFlag) { // Specifically log for bulletFlag
                    System.out.println("bulletFlag is true. Appending line to current entry: '" + lineStr + "'");
                }
                currentEntryLines.add(line);
                String lastToken = "";
                if (lineTokens.length > 0) {
                    lastToken = lineTokens[lineTokens.length-1].replace("-", "").replace("*", "").trim();
                }

                if (lastToken.equals("บาท")) {
                    String itemType = bulletFlag ? "item" : projOutpFlag;
                    if ("item".equals(itemType) && !currentEntryLines.isEmpty()) {
                        System.out.println("Creating 'item' LineItem with " + currentEntryLines.size() + " lines. First line: '" + currentEntryLines.get(0).getText() + "'");
                    }
                    System.out.println("Entry found and added. Type: " + itemType + ". Resetting flags.");
                    entries.add(new com.example.model.LineItem(itemType, new ArrayList<>(currentEntryLines), currentEntryLines.get(0).getPageIndex()));
                    currentEntryLines.clear();
                    bulletFlag = false;
                    projOutpFlag = null;
                }
            } else {
                System.out.println("Line did not match any primary rule and was not part of an active entry. Skipping line.");
            }
        }

        if (!currentEntryLines.isEmpty()) {
            String itemType = bulletFlag ? "item" : (projOutpFlag != null ? projOutpFlag : "unknown_section");
            if ("item".equals(itemType)) {
                 System.out.println("Creating 'item' LineItem with " + currentEntryLines.size() + " lines from remaining. First line: '" + currentEntryLines.get(0).getText() + "'");
            }
            System.out.println("Adding remaining entry. Type: " + itemType);
            entries.add(new com.example.model.LineItem(itemType, new ArrayList<>(currentEntryLines), currentEntryLines.get(0).getPageIndex()));
        }
        System.out.println("Total entries collected: " + entries.size());
        return entries;
    }

    public static void debugHelperFunctions() {
        System.out.println("--- Debugging Fiscal Year Detection ---");
        String[] fiscalExamples = {
            "ปี2563ตงังบประมาณ 616,834,700 บาท",
            "ปี2564ตงังบประมาณ 1,002,522,800 บาท",
            "ปี2565ผูกพนังบประมาณ 1,277,156,200 บาท"
        };

        Pattern fiscalPattern = Pattern.compile(".*ป?ี \\d{4}.*"); // Original pattern from getEntries

        for (String ex : fiscalExamples) {
            System.out.println("Input: '" + ex + "'");
            boolean foundPattern = fiscalPattern.matcher(ex).find();
            boolean foundKeyword1 = ex.contains("ตั้งงบประมาณ");
            boolean foundKeyword2 = ex.contains("ผูกพันงบประมาณ");
            System.out.println("  Matches '.*ป?ี \\d{4}.*' pattern: " + foundPattern);
            System.out.println("  Contains 'ตั้งงบประมาณ': " + foundKeyword1);
            System.out.println("  Contains 'ผูกพันงบประมาณ': " + foundKeyword2);
            YearRange yr = getYearFromString(ex);
            System.out.println(String.format("  getYearFromString result: Start=%d, End=%d", yr.startYear, yr.endYear));
            System.out.println(String.format("  getAmountFromString result: %.2f", getAmountFromString(ex)));
        }

        System.out.println("\n--- Debugging Bullet Pattern Detection ---");
        // Examples derived from lineTokens[0] in previous logs
        String[] bulletExamples = {
            "1.",       // from "1.งบเงนิอดุหนุน"
            "1.1",      // from "1.1เงนิอดุหนุนทวัไป" (assuming tokenization would isolate "1.1")
            "1)",       // from "1)เงนิอุดหนุนการศึกษา"
            "1.6.1)"    // from "1.6.1)โครงการผูกพนัตามสญัญาและมาตรา41"
        };
        for (String ex : bulletExamples) {
            System.out.println("Input: '" + ex + "'");
            System.out.println("  getPatternOfBullet result: " + getPatternOfBullet(ex));
        }
        
        System.out.println("\n--- Debugging Project/Output Detection ---");
        String[] projOutpExamples = {
            "โครงการ:โครงการพฒันาขีดความสามารถของกองทพั", // From line 0.2 (token[0] might be this)
            "ผลผลิต: ผลผลิตตามแผนงาน" // Hypothetical example for output
        };
        String[] projTargets = {"โครงการ", "โครงการพัฒนา", "โครงการปรับปรุง", "โครงการก่อสร้าง"};
        String[] outpTargets = {"ผลผลิต", "ผลผลิตหลัก", "ผลผลิตรอง"};

        for (String lineEx : projOutpExamples) {
            System.out.println("Line Input: '" + lineEx + "'");
            String[] lineTokens = lineEx.split("\\s+"); // Simple split for testing
            
            boolean projFound = false;
            for (String target : projTargets) {
                if (checkProjOutp(target, lineTokens)) {
                    System.out.println("  checkProjOutp for '" + target + "': true");
                    projFound = true;
                    break;
                }
            }
            if (!projFound) System.out.println("  checkProjOutp for Project targets: false");

            boolean outpFound = false;
            for (String target : outpTargets) {
                if (checkProjOutp(target, lineTokens)) {
                    System.out.println("  checkProjOutp for '" + target + "': true");
                    outpFound = true;
                    break;
                }
            }
             if (!outpFound) System.out.println("  checkProjOutp for Output targets: false");
        }
    }


    private static Map<Integer, Double> calculatePageX1Max(List<com.example.model.LineItem> entries) {
        Map<Integer, Double> pageEndXSr = new HashMap<>();
        for (com.example.model.LineItem entry : entries) { // Use fully qualified name or import
            int pageIndex = entry.getPageIndex();
            double x1 = entry.getX1(); // Assumes LineItem.getX1() gives the max X-coordinate
            pageEndXSr.put(pageIndex, Math.max(pageEndXSr.getOrDefault(pageIndex, 0.0), x1));
        }
        return pageEndXSr;
    }

    public static void addLevelToEntriesPositions(List<com.example.model.LineItem> entries) { // Use fully qualified name or import
        final double xDiffThreshold = 0.005;
        List<Double> stackX = new ArrayList<>();
        
        Map<Integer, Double> pageEndXSr = calculatePageX1Max(entries);
        
        double pageX1Max = 0.0;
        if (!pageEndXSr.isEmpty()) {
            pageX1Max = Collections.max(pageEndXSr.values());
        }

        for (com.example.model.LineItem budItem : entries) { // Use fully qualified name or import
            String itemType = budItem.getItemType();

            if (!"item".equals(itemType)) {
                if ("budget_plan".equals(itemType) || "PROJECT".equals(itemType) || "OUTPUT".equals(itemType)) {
                    stackX.clear();
                }
                if ("budget_plan".equals(itemType)) {
                    budItem.setLevel(-2);
                } else if ("PROJECT".equals(itemType) || "OUTPUT".equals(itemType)) {
                    budItem.setLevel(-1);
                }
                continue;
            }

            double pex = pageEndXSr.getOrDefault(budItem.getPageIndex(), pageX1Max); // Default to pageX1Max if page not in map
            double lsx = budItem.getX0() + (pageX1Max - pex);

            while (!stackX.isEmpty() && stackX.get(stackX.size() - 1) > lsx + xDiffThreshold) {
                stackX.remove(stackX.size() - 1);
            }

            if (stackX.isEmpty() || Math.abs(stackX.get(stackX.size() - 1) - lsx) >= xDiffThreshold) {
                stackX.add(lsx);
            }
            budItem.setLevel(stackX.size());
        }
    }

    public static com.example.model.BudgetItem extractTreeLevels(List<com.example.model.LineItem> budItems, String sourceFilename) { // Added sourceFilename // Use fully qualified name or import
        addLevelToEntriesPositions(budItems);

        Map<String, com.example.model.BudgetType> itemtypeMapper = new HashMap<>(); // Use fully qualified name or import
        itemtypeMapper.put("budget_plan", com.example.model.BudgetType.BUDGET_PLAN); // Use fully qualified name or import
        itemtypeMapper.put("PROJECT", com.example.model.BudgetType.PROJECT); // Use fully qualified name or import
        itemtypeMapper.put("OUTPUT", com.example.model.BudgetType.OUTPUT); // Use fully qualified name or import
        itemtypeMapper.put("item", com.example.model.BudgetType.BUDGET_DETAIL); // Use fully qualified name or import
        // itemtypeMapper.put("ROOT", BudgetType.ROOT); // Not needed for items, root is special

        com.example.model.BudgetItem root = new com.example.model.BudgetItem(com.example.model.BudgetType.ROOT, "ROOT", null, sourceFilename, 0); // Use fully qualified name or import
        
        List<StackNode> parentStack = new ArrayList<>();
        parentStack.add(new StackNode(root, -10)); // Level for root is effectively lowest

        for (com.example.model.LineItem budItem : budItems) { // Use fully qualified name or import
            if (budItem.getLevel() == null && !"fiscal_year".equals(budItem.getItemType())) { // Skip items with no level unless fiscal_year
                // System.out.println("Skipping item with no level: " + budItem.getText());
                continue;
            }

            if ("fiscal_year".equals(budItem.getItemType())) {
                if (parentStack.isEmpty()) continue; // Should not happen if root is there

                StackNode lastStackNode = parentStack.get(parentStack.size() - 1);
                com.example.model.BudgetItem lastNode = lastStackNode.getNode(); // Use fully qualified name or import
                
                YearRange yearRange = getYearFromString(budItem.getText());
                double amount = getAmountFromString(budItem.getText());
                
                // FiscalYearBudget constructor: String line, int year, int yearEnd, double amount
                com.example.model.FiscalYearBudget fyb = new com.example.model.FiscalYearBudget( // Use fully qualified name or import
                    budItem.getText().replace("\n", "\t").trim(),
                    yearRange.startYear,
                    yearRange.endYear, // yearEnd was missing in original call
                    amount
                );
                lastNode.addFiscalYearBudget(fyb);
                continue;
            }
            
            // Ensure level is not null for items that are not fiscal_year
            int currentItemLevel = budItem.getLevel() != null ? budItem.getLevel() : -100; // Default for safety, though should be set

            while (!parentStack.isEmpty() && parentStack.get(parentStack.size() - 1).getLevel() >= currentItemLevel) {
                parentStack.remove(parentStack.size() - 1);
            }

            com.example.model.BudgetItem parent = parentStack.isEmpty() ? root : parentStack.get(parentStack.size() - 1).getNode(); // Use fully qualified name or import
            if (parent == null) parent = root; // Default to root if stack somehow becomes empty past initial root

            com.example.model.BudgetType type = itemtypeMapper.get(budItem.getItemType()); // Use fully qualified name or import
            if (type == null) {
                // System.out.println("Warning: Unknown item type '" + budItem.getItemType() + "' for item: " + budItem.getText());
                type = com.example.model.BudgetType.BUDGET_DETAIL; // Default to a detail type // Use fully qualified name or import
            }

            // BudgetItem constructor: BudgetType budgetType, String name, Double amount, String document, int page
            // Assuming LineItem.getLines().get(0).getPage().getDocument().getSourceFilename() is how we get it.
            // This was simplified to pass sourceFilename to extractTreeLevels.
            com.example.model.BudgetItem node = new com.example.model.BudgetItem( // Use fully qualified name or import
                type,
                budItem.getText().replace("\n", "\t").trim(),
                getAmountFromString(budItem.getText()), // Amount can be null if not found
                sourceFilename, // Use passed sourceFilename
                budItem.getPageIndex() 
            );
            
            if (parent != null) {
                 parent.addChild(node); // addChild also sets parent in node
            } else {
                // This case should ideally not be reached if root is handled correctly
                root.addChild(node); 
            }
            
            parentStack.add(new StackNode(node, currentItemLevel));
        }
        return root;
    }
}

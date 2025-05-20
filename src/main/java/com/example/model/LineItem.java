package com.example.model;

import java.util.List;
import java.util.stream.Collectors;

public class LineItem {
    private String itemType;
    private List<LineText> lines;
    private int pageIndex;
    private Integer level;

    public LineItem(String itemType, List<LineText> lines, int pageIndex) {
        this.itemType = itemType;
        this.lines = lines;
        this.pageIndex = pageIndex;
    }

    public String getItemType() {
        return itemType;
    }

    public List<LineText> getLines() {
        return lines;
    }

    public int getPageIndex() {
        return pageIndex;
    }

    public Integer getLevel() {
        return level;
    }

    public void setLevel(Integer level) {
        this.level = level;
    }

    public String getText() {
        if (lines == null || lines.isEmpty()) {
            return "";
        }
        return lines.stream().map(LineText::getText).collect(Collectors.joining(" "));
    }

    public double getX0() {
        if (lines == null || lines.isEmpty()) {
            return 0;
        }
        return lines.stream()
                .filter(line -> line.getWords() != null && !line.getWords().isEmpty())
                .mapToDouble(LineText::getX0)
                .min()
                .orElse(0);
    }

    public double getX1() {
        if (lines == null || lines.isEmpty()) {
            return 0;
        }
        return lines.stream()
                .filter(line -> line.getWords() != null && !line.getWords().isEmpty())
                .mapToDouble(LineText::getX1)
                .max()
                .orElse(0);
    }
}

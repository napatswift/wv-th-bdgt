package com.example.model;

import java.util.List;
import java.util.stream.Collectors;

public class PageText {
    private List<LineText> lines;
    private int pageIndex;
    private double width;
    private double height;
    private boolean isImage;
    private DocumentText document;

    public PageText(List<LineText> lines, int pageIndex, double width, double height, boolean isImage) {
        this.lines = lines;
        this.pageIndex = pageIndex;
        this.width = width;
        this.height = height;
        this.isImage = isImage;
    }

    public List<LineText> getLines() {
        return lines;
    }

    public int getPageIndex() {
        return pageIndex;
    }

    public double getWidth() {
        return width;
    }

    public double getHeight() {
        return height;
    }

    public boolean isImage() {
        return isImage;
    }

    public DocumentText getDocument() {
        return document;
    }

    public void setDocument(DocumentText document) {
        this.document = document;
    }

    @Override
    public String toString() {
        return lines.stream().map(LineText::getText).collect(Collectors.joining("\n"));
    }
}

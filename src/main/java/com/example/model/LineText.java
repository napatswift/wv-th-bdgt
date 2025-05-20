package com.example.model;

import java.util.List;
import java.util.stream.Collectors;

public class LineText {
    private List<WordText> words;
    private int pageIndex;
    private int lineIndex;
    private PageText page;

    public LineText(List<WordText> words, int pageIndex, int lineIndex) {
        this.words = words;
        this.pageIndex = pageIndex;
        this.lineIndex = lineIndex;
    }

    public List<WordText> getWords() {
        return words;
    }

    public int getPageIndex() {
        return pageIndex;
    }

    public int getLineIndex() {
        return lineIndex;
    }

    public PageText getPage() {
        return page;
    }

    public void setPage(PageText page) {
        this.page = page;
    }

    public String getText() {
        return words.stream().map(WordText::getText).collect(Collectors.joining(" "));
    }

    public double getX0() {
        if (words == null || words.isEmpty()) {
            return 0;
        }
        return words.stream().mapToDouble(WordText::getX0).min().getAsDouble();
    }

    public double getY0() {
        if (words == null || words.isEmpty()) {
            return 0;
        }
        return words.stream().mapToDouble(WordText::getY0).min().getAsDouble();
    }

    public double getX1() {
        if (words == null || words.isEmpty()) {
            return 0;
        }
        return words.stream().mapToDouble(WordText::getX1).max().getAsDouble();
    }

    public double getY1() {
        if (words == null || words.isEmpty()) {
            return 0;
        }
        return words.stream().mapToDouble(WordText::getY1).max().getAsDouble();
    }
}

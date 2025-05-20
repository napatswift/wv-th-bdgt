package com.example.model;

import java.util.List;
import java.util.stream.Collectors;

public class DocumentText {
    private List<PageText> pages;
    private String producer;
    private String title;
    private String creator;
    private String subject;
    private String author;
    private String keywords;
    private String sourceFilename;

    public DocumentText(List<PageText> pages, String producer, String title, String creator, String subject, String author, String keywords, String sourceFilename) {
        this.pages = pages;
        this.producer = producer;
        this.title = title;
        this.creator = creator;
        this.subject = subject;
        this.author = author;
        this.keywords = keywords;
        this.sourceFilename = sourceFilename;

        for (PageText page : pages) {
            page.setDocument(this);
        }
    }

    public List<PageText> getPages() {
        return pages;
    }

    public String getProducer() {
        return producer;
    }

    public String getTitle() {
        return title;
    }

    public String getCreator() {
        return creator;
    }

    public String getSubject() {
        return subject;
    }

    public String getAuthor() {
        return author;
    }

    public String getKeywords() {
        return keywords;
    }

    public String getSourceFilename() {
        return sourceFilename;
    }

    @Override
    public String toString() {
        return pages.stream().map(PageText::toString).collect(Collectors.joining("\n\n"));
    }
}

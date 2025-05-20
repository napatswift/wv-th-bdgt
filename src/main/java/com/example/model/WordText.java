package com.example.model;

public class WordText {
    private double x0, y0, x1, y1;
    private String text;

    public WordText(double x0, double y0, double x1, double y1, String text) {
        this.x0 = x0;
        this.y0 = y0;
        this.x1 = x1;
        this.y1 = y1;
        this.text = text;
    }

    public double getX0() {
        return x0;
    }

    public double getY0() {
        return y0;
    }

    public double getX1() {
        return x1;
    }

    public double getY1() {
        return y1;
    }

    public String getText() {
        return text;
    }

    @Override
    public String toString() {
        return text;
    }
}

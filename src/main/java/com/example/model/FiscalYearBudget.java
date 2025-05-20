package com.example.model;

import java.util.HashMap;
import java.util.Map;

public class FiscalYearBudget {
    private String line;
    private int year;
    private int yearEnd;
    private double amount;

    public FiscalYearBudget(String line, int year, int yearEnd, double amount) {
        this.line = line;
        this.year = year;
        this.yearEnd = yearEnd;
        this.amount = amount;
    }

    public String getLine() {
        return line;
    }

    public int getYear() {
        return year;
    }

    public int getYearEnd() {
        return yearEnd;
    }

    public double getAmount() {
        return amount;
    }

    public Map<String, Object> toJson() {
        Map<String, Object> jsonMap = new HashMap<>();
        jsonMap.put("line", line);
        jsonMap.put("year", year);
        jsonMap.put("year_end", yearEnd);
        jsonMap.put("amount", amount);
        return jsonMap;
    }
}

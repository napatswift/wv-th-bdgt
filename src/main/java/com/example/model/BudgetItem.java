package com.example.model;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.stream.Collectors;

public class BudgetItem {
    private BudgetType budgetType;
    private String name;
    private Double amount;
    private String document;
    private int page;
    private List<BudgetItem> children = new ArrayList<>();
    private List<FiscalYearBudget> fiscalYearBudget = new ArrayList<>();
    private BudgetItem parent;

    public BudgetItem(BudgetType budgetType, String name, Double amount, String document, int page) {
        this.budgetType = budgetType;
        this.name = name;
        this.amount = amount;
        this.document = document;
        this.page = page;
    }

    public BudgetItem(BudgetType budgetType, String name, Double amount, String document, int page, BudgetItem parent) {
        this(budgetType, name, amount, document, page);
        this.parent = parent;
    }

    public BudgetType getBudgetType() {
        return budgetType;
    }

    public String getName() {
        return name;
    }

    public Double getAmount() {
        return amount;
    }

    public String getDocument() {
        return document;
    }

    public int getPage() {
        return page;
    }

    public List<BudgetItem> getChildren() {
        return children;
    }

    public List<FiscalYearBudget> getFiscalYearBudget() {
        return fiscalYearBudget;
    }

    public BudgetItem getParent() {
        return parent;
    }

    public void setParent(BudgetItem parent) {
        this.parent = parent;
    }

    public void addChild(BudgetItem child) {
        this.children.add(child);
        child.setParent(this);
    }

    public void addFiscalYearBudget(FiscalYearBudget budget) {
        this.fiscalYearBudget.add(budget);
    }

    public Map<String, Object> toJson() {
        Map<String, Object> jsonMap = new HashMap<>();
        jsonMap.put("budget_type", budgetType.toString());
        jsonMap.put("name", name);
        if (amount != null) {
            jsonMap.put("amount", amount);
        }
        jsonMap.put("document", document);
        jsonMap.put("page", page);
        jsonMap.put("children", children.stream().map(BudgetItem::toJson).collect(Collectors.toList()));
        jsonMap.put("fiscal_year_budget", fiscalYearBudget.stream().map(FiscalYearBudget::toJson).collect(Collectors.toList()));
        return jsonMap;
    }
}

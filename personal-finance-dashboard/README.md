# Personal Finance Dashboard: Cash Flow, Savings Rate & Compounding

**A browser-based tool that turns a month of transactions into a savings rate, then shows what that savings rate compounds to over time.**

▶ **Live demo:** https://kartiktyagi0901-ux.github.io/Projects-/personal-finance-dashboard/

## Features

- **Cash-flow overview:** net worth, income, expenses and savings rate, all updating live as transactions are added or removed
- **Net-worth trend** and a **spending breakdown by category**
- **Compounding projection:** takes this month's surplus as a monthly contribution and projects it forward with adjustable return, horizon and inflation. Shows nominal value, real value (today's money) and how much comes from growth rather than contributions.
- Add and delete transactions, **export to CSV**, with data saved locally in the browser

## The finance behind it

Future value with monthly compounding of an initial balance plus a monthly contribution (an ordinary annuity):

```
FV = NW₀ · (1 + r/12)^(12n) + PMT · [(1 + r/12)^(12n) − 1] / (r/12)
Real FV = FV / (1 + π)^n
```

With the sample data (a 37% savings rate, 6% return, 20 years, 2% inflation), about **€907k** builds up (≈ €610k in today's money), and almost half of it (≈ €445k) comes from **compounding rather than contributions**. Small changes to the monthly savings rate have outsized long-term effects.

## Tech

A single HTML file using vanilla JS and Chart.js, with no build step. The data shown is illustrative sample data.

*Part of my MSc International Finance project work (HWR Berlin).*

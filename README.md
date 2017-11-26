## Microdatasystem - A Data Comparison System

### Skill Used: 
1. Python wrapper of C++ library <a href="https://github.com/leeyilin/CompressLib">CompressLib</a>;
2. build a web server via framework flask;
3. web crawling with Python;
4. JavaScript, including JQuery, DataTable and other plugins.

## Details:
  Quote data provided by different vendors could differ at the same moment of the trade day. Worse still, 
our servers with the same code could generate different quote data at the same time either. By comparing our data 
with different vendors and comparing the data of our servers, we could adjust our data and provide data with higher 
quality. The comparison summary and result, executed every trading day through crontab, are displayed at the front-end
through browser and are also sent to the leaders via emails.

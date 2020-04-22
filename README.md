# Ptt-crawling
Ptt article crawling system with MongoDB, Redis, Scrapy and Spiderkeeper

## 機器配置
- Master
  - 服務: MongoDB, Redis, Spiderkeeper
  - 用途：使用 Spiderkeeper提供 web介面部署以及監控 spider、使用 MongoDB儲存資料、使用 Redis紀錄爬取狀況
- Spider
  - 服務: Scrapyd 
  - 用途： 實際執行爬蟲的主機

## 安裝流程
- **Master**
  1. 下載專案
  ```
  $ git clone https://github.com/ssumaYC/ptt-crawling.git
  ```
  2. 切換至 ptt-crawling/ptt-crawling
  ```
  $ cd ptt-crawling/ptt-crawling/
  ```
  3. 修改 spiderkeeper/Dockerfile，填入 spider機器們的IP
  ```
  CMD [ "--server=http://spider1:6800", "--server=http://spider2:6800" ]
  ```
  5. 使用 docker建立所需的 docker images
  ```
  $ docker-compose build
  ```
  4. 啟動所需服務
  ```
  $ docker-compose up
  ```
- **Spider**
  1. 下載 docker image
  ```
  $ docker pull ssuma/scrapyd
  ```
  2. 啟動 scrapyd
  ```
  $ docker run --rm -p 6800:6800
  ```
- **產生並上傳 .egg檔**
  1. 在本機端下載專案
  ```
  $ git clone https://github.com/ssumaYC/ptt-crawling.git
  ```
  2. 安裝 pipenv
  ```
  $ pip install pipenv
  ```
  3. 切換至 ptt-crawling/ptt-spider/
  ```
  $ cd ptt-crawling/ptt-spider/
  ```
  4. 安裝虛擬環境並啟動虛擬環境
  ```
  $ pipenv install
  $ pipenv shell
  ```
  5. 產生 .egg檔
  ```
  $ cd ptt_spider/
  $ scrapyd-deploy --build-egg egg_file_name.egg
  ```
  6. 上傳 .egg檔
  ```
  拜訪: 

  - http://master:5000 
  - ID: admin
  - password: admin

  1. 創建專案

  2. 上傳 .egg
  ```
## 啟動爬蟲
- **建立新的爬蟲工作**
  1. 拜訪 http://master:5000
  2. 點選右上方 'RUN'按鈕
  3. Spider下拉選單選取 crawl_article
  4. Args 填入
  ```
  start=20200423,end=20200423,job_id=job_id
  ```
  5. 點選 'create'按鈕
- **恢復停擺的爬蟲工作**
  1. 拜訪 http://master:5000
  2. 點選右上方 'RUN'按鈕
  3. Spider下拉選單選取 crawl_article
  4. Args 填入
  ```
  start=20200423,end=20200423,job_id=job_id,recover=true
  ```
  5. 點選 'create'按鈕

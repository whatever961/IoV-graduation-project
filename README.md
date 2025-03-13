# IoV-graduation-project
This project is for my graduation project. It add more function to Eclipse SUMO to adjust the simulation
## func.py 
Puts the functions that are not so important to see in main function. Like MQTT and detect file format
## weather.py
The main function

## 待辦:
1. 研究天氣變化與駕駛行為關係
2. 找到公開天氣資料的格式並分解出有用的資料 (當天日照、雨量、能見度等)
3. 資料分析後用 "adjustDrivingEnv()" 調整道路與駕駛各變數 (駕駛最大時速、加減速度大小、開車是否激進)
4. 實作 "writeLog()" 將模擬中必要訊息寫進特定log 如車禍、不可預期的錯誤訊息
5. 弄好MQTT的連接與傳遞 (有模板套 不急)
6. 連接SQL並讀寫資料
7. 分析模擬 (大概下學期了)

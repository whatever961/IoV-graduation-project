# IoV-graduation-project
This project is for my graduation project. It add more function to Eclipse SUMO to adjust the simulation
## func.py 
Contain the functions that are not so important to see in main function.
## Simulation.py
The main function. Split all car entities to multiple PCs via MQTT. Wait for all PCs ack back to continue next step.
## OBU.py
Get its own vehicle data and fetch weather data. Then adjust its attributes by weather logic. Ack back to Simulation.py.

## 待辦:
1. ✔️研究天氣變化與駕駛行為關係
2. ✔️找到公開天氣資料的格式並分解出有用的資料 (當天日照、雨量、能見度等)
3. ✔️資料分析後用 "adjustDrivingEnv()" 調整道路與駕駛各變數 (駕駛最大時速、加減速度大小、開車是否激進)
4. ✔️弄好MQTT的連接與傳遞
5. 找出可深入研究的細項: 目前可能選項有
    1. 試錯weather_factor找到最好的heuristic
    2. weather資料會影響通訊效率或增加負擔嗎(measure MQTT packets)
    3. 天氣造成的減速對運輸效率的影響
    4. 有/無天氣資料下的模擬數據比較
    5. 車子根據路況自動重新規劃路線的可能
6. 實作 "writeLog()" 將模擬中必要訊息寫進特定log 如車禍、不可預期的錯誤訊息

#coding:utf-8

import csv
import os
import numpy as np
import matplotlib.pyplot as plt
import cv2

#set variable
#-----------------------------------------------------------------


#CSVのデータセットの構成
#--------------------------------------------------------
DATA_TABLE = {
'date':0,'hour':1,'minute':2,'second':3,'counter':4,
'Cc_X':5,'Cc_Y':6,'Cc_Z':7,'Wc_X':8,'Wc_Y':9,'Wc_Z':10,
'Block_X':11,'Block_Y':12,'Consecution':13
};
#print DATA_TABLE;
#--------------------------------------------------------

#平面座標の一辺の長さ（画素数）
IMG_SIZE = 6000;
#分割グリッドのための分割幅
Separate = 500;
#記録画像サイズ
create_img_side = 40;
create_img_size = create_img_side * (IMG_SIZE / Separate), create_img_side * (IMG_SIZE / Separate) , 3;


#グリッドの出現回数をカウントする辞書
#--------------------------------------
grid_counter = {};
grid_counter_tmp = [];
#グラフ描画用
grid_counter_x = [];
grid_counter_y = [];
counter_xticks = [];
#--------------------------------------
#グリッドに出現している時間をカウントする辞書
#--------------------------------------
grid_timer = {};
#--------------------------------------
#グリッド中の高さ（上下）移動の変化を見る辞書
#--------------------------------------
grid_tall = {};
grid_tall_tmp = {};
#グラフ描画用
grid_tall_x = [];
grid_tall_y = [];
grid_tall_img = np.zeros(create_img_size,dtype=np.uint8);
#--------------------------------------
#軌跡描画用
traffic_line_img = np.zeros(create_img_size,dtype=np.uint8);
#--------------------------------------

#-----------------------------------------------------------------

#グリッドごとの出現回数を計算
#-----------------------------------------------------------------
def calc_grid_frequency():
    global grid_counter_tmp;
    for map_point in grid_counter_tmp:
        grid_counter[str(map_point)] += 1;
    del grid_counter_tmp[:];
#-----------------------------------------------------------------

#グリッドごとの高さ（上下）移動の分散を計算
#-----------------------------------------------------------------
def calc_grid_tall_variance():
    global grid_tall_tmp;
    for tall_data in grid_tall_tmp:
        if(len(grid_tall_tmp[tall_data]) != 0):
            data = np.array(grid_tall_tmp[tall_data],dtype=float);
            grid_tall[tall_data] += np.var(data);
    grid_tall_tmp.clear();
#-----------------------------------------------------------------

# read data from CSV file
#-----------------------------------------------------------------
for var in range(0,6):
    CSV_FILE_NAME = 'store_traffic_vaio_{0}.csv'.format(var);
    csvfile = open(CSV_FILE_NAME,'rb');
    dataReader = csv.reader(csvfile);
    for data in dataReader:
    #    print ','.join(data);

        #移動が途切れたら，一旦計算
        #--------------------------------------------------------
        if(data[DATA_TABLE['Consecution']] == 1 and len(grid_counter_tmp) != 0):
            calc_grid_frequency();
            calc_grid_tall_variance();
        #--------------------------------------------------------

        #グリッドポイントの計算
        #--------------------------------------------------------
        map_point = int(data[DATA_TABLE['Block_Y']]) * (IMG_SIZE / Separate) + int(data[DATA_TABLE['Block_X']]);
        #--------------------------------------------------------

        #初めて出現するグリッドポイントを追加する
        #--------------------------------------------------------
        if(str(map_point) not in grid_counter):
            grid_counter.update({str(map_point):0});
            grid_tall.update({str(map_point):0.0});
        #--------------------------------------------------------

        #グリッドごとの出現回数を計算するためのtmp作成
        #--------------------------------------------------------
        if(str(map_point) not in grid_counter_tmp):
            grid_counter_tmp.append(str(map_point));
        #--------------------------------------------------------

        #グリッドごとの高さ（上下）移動の分散を取るためのtmp
        #--------------------------------------------------------
        if(str(map_point) not in grid_tall_tmp):
            grid_tall_tmp.update({str(map_point):[]});
        else:
            grid_tall_tmp[str(map_point)].append(float(data[DATA_TABLE['Wc_Z']]));
        #--------------------------------------------------------

        #検出点描画
        #--------------------------------------------------------
        center = (int(float(data[DATA_TABLE['Wc_X']]) / Separate * create_img_side),int(float(data[DATA_TABLE['Wc_Y']]) / Separate * create_img_side));
        cv2.circle(traffic_line_img,center,1,(255,0,0));
        #--------------------------------------------------------

    #for文を抜けたら，一旦全部処理にかける
    calc_grid_frequency();
    calc_grid_tall_variance();

    csvfile.close();
    #lines of csv file
    #--------------------------------------------------------
    #    print "len : {0}".format(dataReader.line_num);
    #--------------------------------------------------------

#-----------------------------------------------------------------

#グリッドカウンターの結果を表示する
#show the result of grid_counter
#-----------------------------------------------------------------
for data in sorted(grid_counter):
    grid_counter_x.append(len(grid_counter_x)+1);
    grid_counter_y.append(grid_counter[data]);
    counter_xticks.append(data);
    place = (create_img_side * int(int(data) % (IMG_SIZE/Separate)),create_img_side * int(int(data) / (IMG_SIZE/Separate)));
    color = (grid_counter[data]*30,grid_counter[data]*30,grid_counter[data]*30);
#    cv2.rectangle(grid_tall_img,place,(create_img_side,create_img_side),color,cv2.cv.CV_FILLED);
plt.subplot(2,1,1);
plt.title(u"Grid Counter");
plt.bar(grid_counter_x,grid_counter_y,align="center");
plt.xticks(grid_counter_x,counter_xticks);

print '-Grid Counter-';
#print grid_counter;
#-----------------------------------------------------------------

#グリッド内の高さ（上下）移動の分散の結果を表示する
#show the result of grid_tall
#-----------------------------------------------------------------
for data in sorted(grid_tall):
    grid_tall_x.append(len(grid_tall_x)+1);
    grid_tall_y.append(grid_tall[data]);
    place = (create_img_side * int(int(data) % (IMG_SIZE/Separate)),create_img_side * int(int(data) / (IMG_SIZE/Separate)));
plt.subplot(2,1,2);
plt.title(u"Grid Variance");
plt.bar(grid_tall_x,grid_tall_y,align="center");
plt.xticks(grid_tall_x,counter_xticks);

plt.tight_layout(w_pad = 0.5);
plt.show();

print '-Grid Variance-';
#print grid_tall;
#-----------------------------------------------------------------

#show created imgs
cv2.imshow("Traffic_Line",traffic_line_img);
cv2.imwrite("Traffic_Line.png",traffic_line_img);
cv2.waitKey(0);
cv2.destroyAllWindows();

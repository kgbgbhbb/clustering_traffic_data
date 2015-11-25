#coding:utf-8
#2015-10-22
#2015-11-24 Last Modified

import csv
import os
import numpy as np
import matplotlib.pyplot as plt
import cv2
#from sklearn.cluster import KMeans
from datetime import datetime as dt
import time
import sys
import colorsys
import math

#set variable
#-----------------------------------------------------------------

#start the timer for getting processing_time
start = time.time();
print "setting variables";
#the structure of CSV FILE
#--------------------------------------------------------
DATA_TABLE = {
'date':0,'hour':1,'minute':2,'second':3,'counter':4,
'Cc_X':5,'Cc_Y':6,'Cc_Z':7,'Wc_X':8,'Wc_Y':9,'Wc_Z':10,
'Block_X':11,'Block_Y':12,'Consecution':13
};
#print DATA_TABLE;
#--------------------------------------------------------

#平面座標の一辺の長さ（画素数）
#--------------------------------------
IMG_SIZE = 6000;
#--------------------------------------
#分割グリッドのための分割幅
#--------------------------------------
Separate = 500;
#--------------------------------------
#記録画像サイズ
#--------------------------------------
create_img_side = 40;
create_img_size = create_img_side * (IMG_SIZE / Separate), create_img_side * (IMG_SIZE / Separate) , 3;
create_img_size_gray = create_img_side * (IMG_SIZE / Separate), create_img_side * (IMG_SIZE / Separate) , 1;
#--------------------------------------

#グリッドの出現回数をカウントする辞書
#--------------------------------------
grid_counter = {};
grid_counter_tmp = [];
#データ可視化用
grid_count_img = np.zeros(create_img_size,dtype=np.uint8);
#--------------------------------------
#グリッドに出現している時間をカウントする辞書
#--------------------------------------
grid_timer = {};
#--------------------------------------
#グリッド中の高さ（上下）移動の変化を見る辞書
#--------------------------------------
grid_tall = {};
grid_tall_tmp = {};
#データ可視化用
grid_tall_img = np.zeros(create_img_size,dtype=np.uint8);
#--------------------------------------
#軌跡消失点を記録する
#--------------------------------------
vanishment_point = {};
vanishment_point_tmp = "";
#--------------------------------------
#滞在時間計測用
#--------------------------------------
timespan = {};
timespan_tmp = {};
s_datetime = "";
e_datetime = "";
timespan_img = np.zeros(create_img_size_gray,dtype=np.uint8);
#--------------------------------------
#軌跡描画用
#--------------------------------------
traffic_line_img = np.zeros(create_img_size,dtype=np.uint8);
#--------------------------------------
#cluster img
#--------------------------------------
clustering_img = np.zeros(create_img_size,dtype=np.uint8);
#--------------------------------------
#描画動画の生成
#--------------------------------------
videomaker = cv2.VideoWriter('clustering.avi',cv2.cv.CV_FOURCC('M','J','P','G'), 10.0, (create_img_side * (IMG_SIZE / Separate),create_img_side * (IMG_SIZE / Separate)));
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
#人数依存になっている可能性があるため，棄却
#-----------------------------------------------------------------
def calc_grid_tall_variance():
    global grid_tall_tmp;
    for tall_data in grid_tall_tmp:
        if(len(grid_tall_tmp[tall_data]) != 0):
            data = np.array(grid_tall_tmp[tall_data],dtype=float);
            grid_tall[tall_data] += np.var(data);
    grid_tall_tmp.clear();
#-----------------------------------------------------------------



#消失点登録
#-----------------------------------------------------------------
def calc_vanishment_point():
    global vanishment_point_tmp;
    if(vanishment_point_tmp not in vanishment_point):
        vanishment_point.update({str(vanishment_point_tmp):0});
    vanishment_point[str(vanishment_point_tmp)] += 1;
    vanishment_point_tmp = "";
#-----------------------------------------------------------------

#グリッド滞在時間を加算
#-----------------------------------------------------------------
def calc_grid_stay_time(diff):
    global timespan_tmp;
    count_sum = np.sum(timespan_tmp.values());
    #print timespan_tmp,count_sum;
    if(count_sum > 0):
        for data in timespan_tmp:
            timespan[data] += diff * (timespan_tmp[data]/float(count_sum));
    timespan_tmp.clear();
#-----------------------------------------------------------------

#read data from CSV file
#-----------------------------------------------------------------
print "reading data from CSV file";
for var in range(0,6):
    CSV_FILE_NAME = 'store_traffic_vaio_{0}.csv'.format(var);
    if(not os.path.exists(CSV_FILE_NAME)):
        print "File is Nothing."
        exit();
    csvfile = open(CSV_FILE_NAME,'rb');
    dataReader = csv.reader(csvfile);
    print "{0} :".format(CSV_FILE_NAME),;
    for data in dataReader:
    #    print ','.join(data);
        #移動が途切れたら，一旦計算
        #--------------------------------------------------------
        if(data[DATA_TABLE['Consecution']] == "1" and len(grid_counter_tmp) != 0):
            calc_grid_frequency();
            calc_vanishment_point();
            calc_grid_stay_time((e_datetime-s_datetime).total_seconds());
            s_datetime = "";

        #--------------------------------------------------------

        #グリッドポイントの計算
        #--------------------------------------------------------
        map_point = int(data[DATA_TABLE['Block_Y']]) * (IMG_SIZE / Separate) + int(data[DATA_TABLE['Block_X']]);
        #--------------------------------------------------------

        #グリッドごとの滞在時間を計算するためのTemp
        #--------------------------------------------------------
        if(s_datetime == ""):
            s_datetime = dt.strptime("{0} {1}:{2}:{3}".format(data[DATA_TABLE['date']],data[DATA_TABLE['hour']],data[DATA_TABLE['minute']],data[DATA_TABLE['second']]), '%Y-%m-%d %H:%M:%S');
        e_datetime = dt.strptime("{0} {1}:{2}:{3}".format(data[DATA_TABLE['date']],data[DATA_TABLE['hour']],data[DATA_TABLE['minute']],data[DATA_TABLE['second']]), '%Y-%m-%d %H:%M:%S');
        #グリッドの滞在率を計算するためのtmpを作成
        #--------------------------------------------------------
        if(str(map_point) not in timespan_tmp):
            timespan_tmp.update({str(map_point):0});
        else:
            timespan_tmp[str(map_point)]+=1;
        #--------------------------------------------------------
        #--------------------------------------------------------

        #消失点一時登録をする
        #--------------------------------------------------------
        vanishment_point_tmp = str(map_point);
        #--------------------------------------------------------

        #初めて出現するグリッドポイントを追加する
        #--------------------------------------------------------
        #grid_counterとgrid_tallには，同じkeyが存在
        if(str(map_point) not in grid_counter):
            grid_counter.update({str(map_point):0});
            grid_tall.update({str(map_point):{}});
            for tall in range(0,50):
                grid_tall[str(map_point)].update({tall : 0})
            timespan.update({str(map_point):0.0});
        #--------------------------------------------------------

        #グリッドごとの出現回数を計算するためのtmp作成
        #--------------------------------------------------------
        if(str(map_point) not in grid_counter_tmp):
            grid_counter_tmp.append(str(map_point));
        #--------------------------------------------------------

        #グリッドごとの高さ（上下）の相関を見るためのヒストグラム
        #--------------------------------------------------------
        #if(int(float(data[DATA_TABLE['Wc_Z']]) / 100) not in grid_tall[str(map_point)]):
        #    grid_tall[str(map_point)].update({int(float(data[DATA_TABLE['Wc_Z']]) / 100) : 0})
        #else:
        grid_tall[str(map_point)][int(float(data[DATA_TABLE['Wc_Z']]) / 100)] += 1;
        #grid_tall[str(map_point)][int(data[DATA_TABLE['Wc_Z']]) / 100].append(float(data[DATA_TABLE['Wc_Z']]));
        #--------------------------------------------------------

        #検出点描画
        #--------------------------------------------------------
        center = (int(float(data[DATA_TABLE['Wc_X']]) / Separate * create_img_side),int(float(data[DATA_TABLE['Wc_Y']]) / Separate * create_img_side));
        cv2.circle(traffic_line_img,center,1,(255,0,0));
        #traffic_line_video.write(traffic_line_img);
        #--------------------------------------------------------

    #for文を抜けたら，一旦全部処理にかける
    calc_grid_frequency();
    calc_vanishment_point();
    calc_grid_stay_time((e_datetime-s_datetime).total_seconds());
    s_datetime = "";
    csvfile.close();
    print " done";
    #lines of csv file
    #--------------------------------------------------------
    #    print "len : {0}".format(dataReader.line_num);
    #--------------------------------------------------------

#-----------------------------------------------------------------



#消失点グリッドを表示する
#-----------------------------------------------------------------
def draw_vanishment_point(target_img):
    print '-vanishment_point-';
    vanishment_mean = np.mean(vanishment_point.values());
    for data in sorted(vanishment_point):
        place = (create_img_side * int(int(data) % (IMG_SIZE/Separate)),create_img_side * int(int(data) / (IMG_SIZE/Separate)));
        place2 = (create_img_side * int(int(data) % (IMG_SIZE/Separate))+create_img_side,create_img_side * int(int(data) / (IMG_SIZE/Separate))+create_img_side);
        color = (100,30,150);
        if(vanishment_point[data] > vanishment_mean):
            cv2.rectangle(target_img,place,place2,color,cv2.cv.CV_FILLED);
    return target_img;
#-----------------------------------------------------------------
'''
#グリッドカウンターの結果を表示する
#show the result of grid_counter
#-----------------------------------------------------------------
print '-Grid Counter-';
#print grid_counter;
for data in sorted(grid_counter):
    place = (create_img_side * int(int(data) % (IMG_SIZE/Separate)),create_img_side * int(int(data) / (IMG_SIZE/Separate)));
    place2 = (create_img_side * int(int(data) % (IMG_SIZE/Separate))+create_img_side,create_img_side * int(int(data) / (IMG_SIZE/Separate))+create_img_side);
    color = (grid_counter[data]*100,grid_counter[data]*30,grid_counter[data]*20);
    cv2.rectangle(grid_count_img,place,place2,color,cv2.cv.CV_FILLED);

#-----------------------------------------------------------------

#グリッド内の高さ（上下）移動の分散と滞在時間の混合結果を表示する
#show the result of grid_tall
#-----------------------------------------------------------------
print '-Grid Z_Correlation and Time Span-';
s_scale = int(max(timespan.values()))-int(min(timespan.values()));
for data in sorted(grid_tall):
    place = (create_img_side * int(int(data) % (IMG_SIZE/Separate)),create_img_side * int(int(data) / (IMG_SIZE/Separate)));
    place2 = (create_img_side * int(int(data) % (IMG_SIZE/Separate))+create_img_side,create_img_side * int(int(data) / (IMG_SIZE/Separate))+create_img_side);
    #クラスタリング用の画像もこっそり書き出し
    cv2.rectangle(clustering_img,place,place2,(138,43,226),cv2.cv.CV_FILLED);


#-----------------------------------------------------------------
'''
#Draw grid_lines and grid_numbers
#-----------------------------------------------------------------
def draw_grid_lines_and_numbers(target_img):
    print '-Draw Grid Lines and Numbers-';
    for i in range(0,(IMG_SIZE/Separate)):
        #col
        cv2.line(target_img,(create_img_side*i,0),(create_img_side*i,create_img_side*(IMG_SIZE/Separate)),(255,255,0),1);
        #row
        cv2.line(target_img,(0,create_img_side*i),(create_img_side*(IMG_SIZE/Separate),create_img_side*i),(255,255,0),1);
        for j in range(0,(IMG_SIZE/Separate)):
            draw_point = (i*create_img_side,j*create_img_side+10);
            grid_number = str(i+j*(IMG_SIZE/Separate));
            cv2.putText(target_img,grid_number,draw_point,cv2.FONT_HERSHEY_PLAIN,0.5,(255,190,0));
    return target_img;
#-----------------------------------------------------------------
traffic_line_img = draw_grid_lines_and_numbers(traffic_line_img);
clustering_img = draw_grid_lines_and_numbers(clustering_img);
timespan_img = draw_grid_lines_and_numbers(timespan_img);
grid_tall_img = draw_grid_lines_and_numbers(grid_tall_img);
grid_count_img = draw_grid_lines_and_numbers(grid_count_img);




#さらなる後処理ように，データ出力
#-----------------------------------------------------------------
output_p = open('data.csv', 'ab') #ファイルが無ければ作る、の'a'を指定します
output = csv.writer(output_p)
for data in sorted(grid_tall):
    output.writerow([int(data),timespan[data]]);
    #print int(data),grid_tall[data],timespan[data],grid_counter[data];

#-----------------------------------------------------------------
#Machine Learning Challenge
#-----------------------------------------------------------------
#アホみたいにユークリッド距離を出すプログラム　使えなさすぎ
def calc_Euclidean_distance(base,target):
#    diff_tall = abs(grid_tall[base]/max(grid_tall.values()) - grid_tall[target]/max(grid_tall.values()));
    diff_time = abs(timespan[base]/max(timespan.values()) - timespan[target]/max(timespan.values()));
#    diff_counter = abs(grid_counter[base] - grid_counter[target]);
    #print diff_tall,diff_time;
    return math.sqrt(diff_tall**2 + diff_time**2);

#グリッド間のZ座標データヒストグラムの相関係数を取得
#-----------------------------------------------------------------
def calc_grid_tall_correlation(base,target):
    return np.corrcoef(grid_tall[base].values(), grid_tall[target].values())[0,1];
#-----------------------------------------------------------------

#8近傍クラスタリング関数
#-----------------------------------------------------------------
def start_clustering():
    for data in sorted(grid_tall):
        for v in [-12,0,12]:
            for h in [-1,0,1]:
                if(v==0 and h ==0):
                    continue;
                comp_point = int(data) + v + h;
                if(str(comp_point) in grid_tall):
                #    output.writerow([calc_grid_tall_correlation(data,str(comp_point))]);
                    if(calc_grid_tall_correlation(data,str(comp_point)) >= 0.529291293):
                        point = (create_img_side * int(int(data) % (IMG_SIZE/Separate))+create_img_side/2,create_img_side * int(int(data) / (IMG_SIZE/Separate))+create_img_side/2);
                        point2 = (create_img_side * int(int(comp_point) % (IMG_SIZE/Separate))+create_img_side/2,create_img_side * int(int(comp_point) / (IMG_SIZE/Separate))+create_img_side/2);
                        cv2.line(clustering_img,point,point2,(0,0,255),2);
                        videomaker.write(clustering_img);
#-----------------------------------------------------------------

start_clustering();
#clustering_img = draw_vanishment_point(clustering_img);


#show and save created imgs
#-----------------------------------------------------------------
#cv2.imshow("Traffic_Line",traffic_line_img);
#cv2.imshow("Grid Count",grid_count_img);
#cv2.imshow("Grid Tall",grid_tall_img);
cv2.imwrite("Traffic_Line.png",traffic_line_img);
cv2.imwrite("Grid_Count.png",grid_count_img);
cv2.imwrite("Grid_Tall.png",grid_tall_img);
cv2.imwrite("Grid_Timespan.png",timespan_img);
cv2.imwrite("clustering.png",clustering_img);
cv2.waitKey(0);
cv2.destroyAllWindows();
#-----------------------------------------------------------------

output_p.close();
#stop the timer and show processing_time
elapsed_time = time.time() - start
print ("processing_time:{0}".format(elapsed_time)) + "[sec]"

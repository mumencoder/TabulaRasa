
INSERT INTO accounts(id,login,password,timecreate,timelastmodify,status,priv)\
	VALUES(1000,'admin',PASSWORD('admin'),'2020:06:01 12:00:00',NULL,1,4);
INSERT INTO chars(charid,accid,charname,pos_x,pos_y,pos_z,pos_zone,pos_prevzone,playtime,nation)\
    VALUES(1,1000,'Maincat',0,0,-50,241,241,1,2);
INSERT INTO char_look(charid,face,race,size) VALUES(1,11,7,0);
INSERT INTO char_stats(charid,mjob) VALUES(1,5);
UPDATE chars SET gmlevel = 4 WHERE charname = "Maincat";
CREATE DATABASE himi;
// 定位相关的js
    



//  2、 初始化地图
    var bm = new BMap.Map("container");
    bm.centerAndZoom(new BMap.Point(114.300088,30.619105), 10);
    bm.enableScrollWheelZoom(true);  // 开启鼠标滚轮缩放
    bm.addControl(new BMap.NavigationControl()); //平移缩放
    // bm.addControl(new BMap.ScaleControl()); // 比例尺
    bm.addControl(new BMap.OverviewMapControl());  //缩略地图
    bm.addControl(new BMap.MapTypeControl()); // 地图类型
    bm.addControl(new BMap.GeolocationControl);  // 定位当前位置
    // bm.setCurrentCity("武汉"); // 仅当设置城市信息时，MapTypeControl的切换功能才能可用地图初始化

/*
inside_polygon.js
Googlemap用。多角形エリアの中のポイントかどうかを判定。
Copyright:MasanoriYono
2011/08/26 14:11

使い方サンプル
area_points = [
				new google.maps.LatLng(34.971755107404306,138.38451269374843),
				new google.maps.LatLng(34.971315527197675,138.3856392215347),
				new google.maps.LatLng(34.971878189439444,138.38649216400142),
				new google.maps.LatLng(34.9722254556138,138.3857891540756),
				new google.maps.LatLng(34.973029876664405,138.38626658728026),
				new google.maps.LatLng(34.973482634764736,138.3866689186325),
				new google.maps.LatLng(34.973671649541856,138.38651335050963),
				new google.maps.LatLng(34.97370681503366,138.38634168913268),
				new google.maps.LatLng(34.97317933107133,138.3860198240509),
				new google.maps.LatLng(34.97338153365837,138.38557994177245)
			];
			
google.maps.event.addListener(testMarker, 'drag', function(e){
	$("lat_lng").innerHTML = e.latLng.lat()+ "," + e.latLng.lng();

	var output_str ="";
	var v_count = area_points.length;
	var vec = new Array(v_count);
	//判定対象の点の配列を作成。
	for(var i = 0;i < v_count ;i++){
		vec[i] = {lat:area_points[i].lat(),lng:area_points[i].lng()};
	}
	if(is_InsidePolygon(area_points.length, area_points, {lat:e.latLng.lat(),lng:e.latLng.lng()})){
		output_str += " <font color=red>範囲内です。</font>";
	}
	$("lat_lng").innerHTML += output_str;
}


*/
//座標
function point( lat, lng ){
	this.lat = lat;
	this.lng = lng;
}
// 2つのベクトルから角度を計算
function getRadian(vec0, vec1){
	var dot; 	// 内積
	var d0, d1;	// それぞれのベクトルの長さ
	var cosine;	// コサイン値
	var angle;
	with( Math ){
		dot = vec0.lat * vec1.lat + vec0.lng * vec1.lng;
		d0 = sqrt( vec0.lat * vec0.lat + vec0.lng * vec0.lng );
		d1 = sqrt( vec1.lat * vec1.lat + vec1.lng * vec1.lng );
		cosine = dot / ( d0 * d1 );
		angle = acos( cosine );
	}
	return angle;
}
//2つのベクトルの位置関係を外積から判断。プラス方向は反時計回り。
function getDirection( vec0, vec1){
	var cross;	// 外積
	var d0, d1;	// それぞれのベクトルの長さ
	var sine;	// サイン値
	var angle;
	with( Math ){
		cross = vec0.lat * vec1.lng - vec1.lat * vec0.lng;
		d0 = sqrt( vec0.lat * vec0.lat + vec0.lng * vec0.lng );
		d1 = sqrt( vec1.lat * vec1.lat + vec1.lng * vec1.lng );
		sine = cross / ( d0 * d1 );
		angle = asin( sine );
	}
	if(angle>0){
		return 1;
	}else{
		return  -1;
	}
}
//頂点の配列と判定したい対象点を受け取って判断する関数
function is_InsidePolygon(v_count,vertex,d_point){
//v_count:頂点の数。v_numをセット。
//a_src:頂点の配列。polygon.vertexをセット。
//d_point:判定対象の点。{x:mouseX,y:mouseY}をセット。
	var vec = new Array(v_count);
	//判定対象の点を原点として各頂点を移動した場合の配列を作成。
	for(var i = 0;i < v_count;i++){
		vec[i] = new point( vertex[i].lat - d_point.lat, vertex[i].lng - d_point.lng );
	}
	var angle = 0;
	for( var i = 0;i < v_count;i++ ){
		var rad, sign;
		var c, n;
		c = i;
		//終点の次は配列添字のiでは取れない。最後の処理は始点を使うため。2011/08/26 07:29
		n = i + 1;
		n %= v_count;
		// 2つのベクトルの角度を計算
		rad = getRadian( vec[c], vec[n] );
		// vec[ c ]から見てvec[ n ]が時計回り方向にいるのか反時計回り方向にいるのかチェック
		// 反時計回りが正方向。反時計周りだったらラジアンをプラス、時計回り方向だったらラジアンをマイナス
		// 内部の点なら総和が2πになるはず。ただし小数点の計算なので誤差が出る。
		sign = getDirection( vec[c], vec[n] );
		angle += sign * rad;
	}
	//floatの精度の問題で誤差が出るため、ほんの少し加算。
	if( Math.abs( angle ) + 0.001 >= Math.PI * 2 ){
		return true;
	}else{
		return false;
	}
}
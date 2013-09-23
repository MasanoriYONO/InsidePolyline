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
	if(is_InsidePolygon(v_count, vec, {lat:e.latLng.lat(),lng:e.latLng.lng()})){
		output_str += " <font color=red>範囲内です。</font>";
	}
	$("lat_lng").innerHTML += output_str;
}
*/
eval(function(p,a,c,k,e,r){e=function(c){return(c<a?'':e(parseInt(c/a)))+((c=c%a)>35?String.fromCharCode(c+29):c.toString(36))};if(!''.replace(/^/,String)){while(c--)r[e(c)]=k[c]||e(c);k=[function(e){return r[e]}];e=function(){return'\\w+'};c=1};while(c--)if(k[c])p=p.replace(new RegExp('\\b'+e(c)+'\\b','g'),k[c]);return p}('h s(a,b){m.3=a;m.4=b}h o(a,b){5 c;5 d,6;5 e;5 f;q(8){c=a.3*b.3+a.4*b.4;d=9(a.3*a.3+a.4*a.4);6=9(b.3*b.3+b.4*b.4);e=c/(d*6);f=x(e)}7 f}h k(a,b){5 c;5 d,6;5 e;5 f;q(8){c=a.3*b.4-b.3*a.4;d=9(a.3*a.3+a.4*a.4);6=9(b.3*b.3+b.4*b.4);e=c/(d*6);f=w(e)}l(f>0){7 1}p{7-1}}h v(a,b,d){5 e=r u(a);t(5 i=0;i<a;i++){e[i]=r s(b[i].3-d.3,b[i].4-d.4)}5 f=0;t(5 i=0;i<a;i++){5 g,j;5 c,n;c=i;n=i+1;n%=a;g=o(e[c],e[n]);j=k(e[c],e[n]);f+=j*g}l(8.y(f)+0.z>=8.A*2){7 B}p{7 C}}',39,39,'|||lat|lng|var|d1|return|Math|sqrt||||||||function||sign|getDirection|if|this||getRadian|else|with|new|point|for|Array|is_InsidePolygon|asin|acos|abs|001|PI|true|false'.split('|'),0,{}))
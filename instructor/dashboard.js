/**
 * Created by ChungJungMin on 2015. 10. 28..
 */

<%page args="instructor_dashboard_data" />
<%!
	import json
%>

// going to assume that we always have 'week_1', 'week_2' and 'week_3' for keys
function convertDataFormat(dataArr) {
	var result = {'week_1': {}, 'week_2': {}, 'week_3': {}};
	
	// make item with key = 'group' for each week
	var groupItem = {};
	for (var i = 0; i < dataArr.length; i++) {
		var mygroup = dataArr[i]['group'];
		var myname = dataArr[i]['name'];
		if (mygroup == "Default Group") continue;
		if (! (mygroup in groupItem)) {
			groupItem[mygroup] = [];
		}
		groupItem[mygroup].push(myname);
	}
	for (var key in result) {
		result[key]['group'] = groupItem;
	}
	
	// make item with key = a person's name for each week
	for (var i = 0; i < dataArr.length; i++) {
		var item = dataArr[i];
		var name = item['name'];
		for (var key in result) {
			var newitem = getNewItemPerPerson(item[key]);
			result[key][name] = newitem;
		}
	}
	return result;
}

function getNewItemPerPerson(week_item) {
	var newitem = {"goal": [0, ""], "progress": 0, "v1": 0, "v2": 0, "t1": [0, ""], "t2": [0, ""], "i_solution": 0, "r1": [0,""], "r2": [0,""], "g_solution": 0};

    var goalArr = week_item['goal'];
	if (goalArr['status']) {
		newitem['goal'][0] = 1;
		newitem['goal'][1] = '(목표설정: ' + goalArr['answer']['reason'] + ')';
	}

	// fill in progress
	newitem['progress'] = ((parseFloat(week_item['progress'])/10.0)*100).toFixed(0);

	// fill in v1 and v2
	var videoArr = week_item['video'];
	for (var i = 0; i < videoArr.length; i++) {
		var video_item = videoArr[i];
		perc = parseFloat(video_item['watch_time'])/parseFloat(video_item['total_time'])
		var position = video_item['position']; // this give 'v1' or 'v2'
		newitem[position] = ((perc)*100).toFixed(0)
	}

	// fill in t1 and t2
	var thinkArr = week_item['think'];
	for (var i = 0; i < thinkArr.length; i++) {
		var think_item = thinkArr[i];
		var position = think_item['position']; // this give 't1' or 't2'
		if (think_item['status']) {
			newitem[position][0] = 1;
			newitem[position][1] = '(선택: ' + think_item['answer']['choice'] + ')<br />' + '(이유: ' + think_item['answer']['reason'] + ')';
		}
	}

	// fill in i_solution
	if (week_item['i_solution']['status']) {
		newitem['i_solution'] = 1;
	}

	// fill in r1 and r2
	var refArr = week_item['reflection'];
	for (var i = 0; i < refArr.length; i++) {
		var ref_item = refArr[i];
		var position = ref_item['position']; // this give 'r1' or 'r2'
		if (ref_item['status'] == 1 && position == 'r2') {
			newitem[position][0] = 1;
			newitem[position][1] = '(계획: ' + ref_item['answer']['reason'] + ')';
		}
		else if (ref_item['status'] == 1 && position == 'r1') {
			newitem[position] = 1;
		}
	}
	
	// fill in group
	if (week_item['g_solution']['status']) {
		newitem['g_solution'] = 1;
	}

	return newitem;
}


$(function() {
	var rawinput = ${json.dumps(instructor_dashboard_data)};
	var input = convertDataFormat(rawinput); 
	/**** table ****/

	function Quizhandler(quiz){
	    if (quiz[0] == '0') {return "X";}
	    else {return "O <br> <p>"+quiz[1]+"</p>"}
	}

	function indicator(number){
	    if (number == 0) {return "X"}
	    else {return "O"}
	}

	function createContentHead(weekNum) {
	    var html = "<tr>" +
			    "<th rowspan = '2'> " + weekNum +"주차" +
			    "<th rowspan = '2'>아이디" +
			    "<th rowspan = '2'>이번주<br>학습" +
			    "<th rowspan = '2'>학습목표" +
			    "<th colspan = '2'>강의동영상" +
			    "<th width='25%' colspan = '2'>생각해보기" +
			    "<th colspan = '2'>성찰" +
			    "<th rowspan = '2'>개인해결안" +
			    "<th rowspan = '2'>그룹해결안" +
			"</tr>" +
			"<tr>" +
			    "<th> 1차" +
			    "<th> 2차" +
			    "<th> 1차" +
			    "<th> 2차" +
			    "<th> 설문" +
			    "<th> 계획" +
			"</tr>";

	    return html;
	}

	function createGrouprow(weekinfo, group) {
	    var Members = weekinfo["group"][group];

	    var html = "";
	    for (var i = 0 ; i < Members.length ; i++) {
		var Member = Members[i];

		if (i == 0) {
		    html += "<tr><td rowspan=" + Members.length + ">" + group;
		} else {
		    html += "<tr>";
		}

		html += "<td>" + Member +
			"<td>" + weekinfo[Member]["progress"] +"%" +
			//"<td>" + indicator(weekinfo[Member]["goal"]) +
			"<td>" + Quizhandler(weekinfo[Member]["goal"]) +
			"<td>" + weekinfo[Member]["v1"] +"%" +
			"<td>" + weekinfo[Member]["v2"] +"%" +
			"<td>" + Quizhandler(weekinfo[Member]["t1"]) +
			"<td>" + Quizhandler(weekinfo[Member]["t2"]) +
			"<td>" + Quizhandler(weekinfo[Member]["r1"]) + 
			"<td>" + Quizhandler(weekinfo[Member]["r2"]) +
			//"<td>" + indicator(weekinfo[Member]["r1"]) + 
			//"<td>" + indicator(weekinfo[Member]["r2"]) + 
			"<td>" + indicator(weekinfo[Member]["i_solution"]);
			//"<td>" + indicator(weekinfo[Member]["reflection"]);

		if (i == 0){
		    html += "<td rowspan=" + Members.length +">"
			    + indicator(weekinfo[Member]['g_solution']);
		}

		html += "</tr>";
	    };

	    return html;

	}

	function createTotalGrouprow(week){
	    var html = "";
	    for (var groupName in input[week]['group']) {
		html += createGrouprow(input[week], groupName);
	    }
	    return html;
	}


    var tab = "";

    var weekNum = 1;
    for (var week in input) {
	tab += "<div style='height: 30px; width: 10px'></div><h2>Week " + weekNum + "</h2>" + 
		    "<table class = 'small_table'>" +
		    	createContentHead((weekNum).toString()) +
		    	createTotalGrouprow(week)+
		    "</table>" +
		"";
	weekNum++;
    }

    tab += "";

    $(".table_container").html(tab);
});



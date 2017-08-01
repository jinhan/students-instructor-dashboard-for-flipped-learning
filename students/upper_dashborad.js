/**
 * Created by jihyunlee on 10/8/15.
 */

<%page args="username, dashboard_overview_data"/>
<%!
    import json
%>

$(function () {
    <%
	keys = ['week_1', 'week_2', 'week_3']

	myProgressRate = 0
	avgProgressRate, count = 0, 0
	py_my_dashboard_data = {}

	## calculate myProgressRate, avgProgressRate
	## and also get the dashboard data with my username
	for dash in dashboard_overview_data:
		for week in keys:
			if dash['group'] != 'Default Group':
				avgProgressRate += dash[week]['progress']
				count += 1
		if dash['name'] == username:
			py_my_dashboard_data = dash
			myProgressRate = dash['total_progress']
	if count != 0:
		avgProgressRate /= count
	else:
		avgProgressRate = 0
	
	## handle sections with only one object e.g. goal
	def handleSingleObj(my_dashboard_data, section):
	    py_result = []
	    for week in keys:
		py_result.append([my_dashboard_data[week][section]])
	    return py_result

	## handle sections with two elements
	## they should be sorted by their position keys e.g. video with v1 and v2
	def handleLenTwoArr(my_dashboard_data, section):
	    py_result = []
	    for week in keys:
		py_result.append(sorted(my_dashboard_data[week][section], key=lambda x: x['position']))
	    return py_result

	## 'discussion' is a special case to handle
	def handleDiscussion(my_dashboard_data):
	    py_result = []
	    for week in keys:
		disArr = my_dashboard_data[week]['discussion']
		py_subresult = [{'type': 'question', 'total': 0, 'vote_total': 0}, 
				{'type': 'discussion', 'total': 0, 'vote_total': 0},
				{'type': 'reply', 'total': 0, 'vote_total': 0}]
		for dis in disArr:
		    for sub in py_subresult:
			if sub['type'] == dis['type']:
			    sub['total'] += dis['total']    
			    sub['vote_total'] += dis['vote_total']

		py_result.append(py_subresult)
	    return py_result

    %>

    var purposes = 	${ json.dumps( handleSingleObj(py_my_dashboard_data, 'goal') ) };
    var videos = 	${ json.dumps( handleLenTwoArr(py_my_dashboard_data, 'video') ) };
    var scores = 	${ json.dumps( handleLenTwoArr(py_my_dashboard_data, 'think') ) };
    var assignments = 	${ json.dumps( handleSingleObj(py_my_dashboard_data, 'i_solution') ) };
    var groupassigns = 	${ json.dumps( handleSingleObj(py_my_dashboard_data, 'g_solution') )};
    var reflections = 	${ json.dumps( handleLenTwoArr(py_my_dashboard_data, 'reflection') ) };
    var discussions = 	${ json.dumps( handleDiscussion(py_my_dashboard_data) ) };
//console.log(discussions);

    var myProgress = (${json.dumps( myProgressRate )}*100).toFixed(0)*1;
    var avgProgress = (${json.dumps( avgProgressRate )}*10).toFixed(0)*1;

//    console.log(${json.dumps(dashboard_overview_data)});

/***** TABLE *****/
function createWeeklyCircles(weekArr, type) {
    var html = "<div id = 'tq'>";

    for (var j = 0; j < weekArr.length; j++) {
        var onebox = weekArr[j];
        var status = "White";
	
	if (type == "videos") {
	    if (onebox['status'] == 1) {
		status = "Yellow";
	    } else if (onebox['status'] == 2) {
		status = "Green";
	    }
        } else {
            if (onebox['status']) {
                status = "Green";
            }
        }

        var classname = "onebox" + " box" + type;
        if (j == weekArr.length -1) {
            classname += " endweek" ;
        }

        /* changed here jungmin */
        html += "<div title='" + onebox['display_name'] + "' class='" + classname +
            "'><div class = 'circle status" + status +"'></div></div>";
    }

    html += "</div>";
    return html;
}

function createWeeklyRow(overallArr, title, type) {
    var html = "<tr>" +
                "<td>" + title;
    for (var i = 0; i < overallArr.length; i++) {
        html += "<td>" + createWeeklyCircles(overallArr[i], type);
    }

    for (var i = overallArr.length; i < 3; i++) {
        html += "<td>";
    }

    html += "</tr>";
    return html;
}

/* calc Activity (i.e. sum of 'total') or Like (i.e. sum of 'vote_total') */
function calcDiscussion(discussionBigArr, title ) {
    var html = "<tr>" +
                "<td>" + title ;
    for (var i = 0; i < discussionBigArr.length; i++) {
        var like = 0;
        var count = 0 ;
        var weeklyDiscussion = discussionBigArr[i];
        for (var j = 0; j < weeklyDiscussion.length; j++) {
            var OnePost = weeklyDiscussion[j];
            like += parseInt(OnePost['vote_total']);
            count += parseInt(OnePost['total']);
        }

        html += "<td>" + "<div>" + "게시물 " + count + "개 <br>" + "좋아요 "+ like + "개" + "</div>";
    }

    html += "</tr>";
    return html
}

function findLengthArr(arr) {
    var count = 0;
    for (var i = 0; i < arr.length; i++) {
        for (var j = 0; j < arr[i].length; j++) {
            count += 1;
        }
    }
    return count;
}

    var purposerow = createWeeklyRow(purposes, '목표설정', 'purposes');
    var videorow = createWeeklyRow(videos, '강의동영상', 'videos');
    var scorerow = createWeeklyRow(scores, '생각해보기', 'scores');
    var assignmentrow = createWeeklyRow(assignments, '개인해결안', 'assignments');
    var reflectionrow = createWeeklyRow(reflections, '성찰', 'reflections');
    var grouptassignrow = createWeeklyRow(groupassigns, '그룹해결안', 'groupassigns');
    var discussionrow = calcDiscussion(discussions, '질의응답');

    var tab = "<table class = 'table'>"+
                    "<tr><th colspan='4'> 나의 학습 현황 </tr>"+
                    "<tr class = 'week_id'>"+
                        "<td>"+
                        "<td>1주차<td>2주차<td>3주차" +
                    "</tr>";
    tab += purposerow + videorow + scorerow + assignmentrow + grouptassignrow + reflectionrow + discussionrow;
    tab +=  "</table>"
    $( "#upper_table" ).html( tab );

    makePieChart(avgProgress, myProgress);

});

function makePieChart(avgProgress, myProgress) {

	/***** PIE CHART *****/
	var data = [    { label: "progress",  data: avgProgress, color: "#4D7FC7"},
			{ label: "rest",  data: 100-avgProgress, color: "#f5f5f5"}
		    ];
	var my_data = [    { label: "progress",  data: myProgress, color: "#80D7F8"},
			{ label: "rest",  data: 100-myProgress, color: "#f5f5f5"}
		    ];

	$.plot('#upper_piechart', data, {
	    series: {
		pie: {
		    show: true,
		    radius:1,
		    label: {
			show: true,
			radius: 3/4,
			background: {
			    opacity: 0.5
			},
			formatter: function(label, series) {
			    if (label == "progress") {
				return '<div style="font-size:12pt; text-align:center; padding: 2px; color: black;">'
				    + series.data[0][1] + '%</div>';
			    }
			    return "";
			}
		    }
		}
	    },
	    legend: {
		show: false
	    }
	});

	$.plot('#pie', my_data, {
	    series: {
		pie: {
		    show: true,
		    radius: 0.6,
		    label: {
			show: true,
			radius: 2/5,
			background: {
			    opacity: 0
			},
			formatter: function(label, series) {
			    if (label == "progress") {
				return '<div style="font-size:12pt; text-align:center; padding: 2px; color: black;">'
				    + series.data[0][1] + '%</div>';
			    }
			    return "";
			}
		    }
		}
	    },
	    legend: {
		show: false
	    }
	});

	$('#pie').appendTo("#upper_piechart");
	$('#upper_piechart canvas').css('position', 'absolute');

}

/***** legends *****/
function maketableCircle(color){
    var html = "<div class = 'align circle status"
    html += color +"'>"
    html += "</div>"

    return html
}


function makepieCircle(color){
    var html = "<div class = 'align circle' style = 'color : #"
    html += color + "; background-color : #"
    html += color + "'>"
    html += "</div>"

    return html
}

function makeComment(comment){
    var html = "<div class = 'align'>"
    html += comment
    html += "</div>"

    return html
}

$(function() {
    var html = "<div id = 'pie_legend'>"+
                    "<div id = 'legendsmallbox'>" + makepieCircle("80D7F8") + makeComment(" 나의 진도율") + "</div>" +
                    "<div id = 'legendsmallbox'>" + makepieCircle("4D7FC7") + makeComment(" 수강생 평균 진도율") + "</div>" +
                "</div>"+
                "<div id = 'table_legend'>"+
                    "<div id = 'legendsmallbox'>" + maketableCircle("Green") + makeComment(" 완료") + "</div>" +
                    "<div id = 'legendsmallbox'>" + maketableCircle("Yellow") + makeComment(" 학습중") + "</div>" +
                    "<div id = 'legendsmallbox'>" + maketableCircle("White") + makeComment(" 미완료") + "</div>" +
                "</div>"
    $( ".legends" ).html( html );

})

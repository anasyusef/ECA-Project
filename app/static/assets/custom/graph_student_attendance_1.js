var current_url_array = window.location.href.split('/');

$.ajax({

    type:'GET',
    url: current_url_array.slice(0,3).join('/') +  '/api/view_attendance_detail/' +
    current_url_array[current_url_array.length - 2] +
        '/' + current_url_array[current_url_array.length - 1],
    timeout:2000,
    dataType: 'json',
    success: function(data) {

    if (data['percentage_attendance_true'] == 0 && data['percentage_attendance_false'] == 0) {

        $('#chartPreferences').html('<p class="text-center font-weight-bold">There is no sufficient data to produce the graph</p>');

    }

    else {

        var dataPreferences = {
            series: [
                [25, 20, 20, 25]
            ]
        };

        var optionsPreferences = {
            donut: true,
            donutWidth: 40,
            startAngle: 0,
            total: 100,
            showLabel: false,
            axisX: {
                showGrid: false
            }
        };

        Chartist.Pie('#chartPreferences', dataPreferences, optionsPreferences);

        Chartist.Pie('#chartPreferences', {
            labels: [Math.round(data['percentage_attendance_true']) + '%', Math.round(data['percentage_attendance_false']) + '%'],
            series: [data['percentage_attendance_true'], data['percentage_attendance_false']]
        });
        }
    }

});
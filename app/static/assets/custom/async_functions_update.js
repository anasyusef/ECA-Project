$(document).ready(function() {

    $.ajax({

        type:'GET',
        url:'/eca_info',
        timeout:2000,
        dataType: 'json',
        data: 'eca=' + $('#eca_name').val(),
        success: function(data) {
            $('#day_eca').val(data['day'].toLowerCase());
        }

    });

    }
);
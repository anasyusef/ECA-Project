// AJAX is called twice to ensure that it is called as soon as the page loads and the it is also called when the
// dropdown menu is changed


$('#eca_name').on('change', function() {

    if (this.value != 'choose') {
        $.ajax({

            type:'GET',
            url:'/eca_info',
            timeout:2000,
            dataType: 'json',
            data: 'eca=' + $('#eca_name').val(),
            success: function(data) {
                $('#eca_day').val(data['day']);
                $('#eca_organiser').val(data['organiser']);
                $('#eca_start_time').val(data['start_time']);
                $('#eca_end_time').val(data['end_time']);
                $('#eca_location').val(data['location']);
                $('#eca_brief_description').val(data['brief_description']);
                $('#eca_essentials').val(data['essentials']);
                $('#eca_organiser_email_address').val(data['email_address']);

                if (data['students_enrolled'] == data['max_people']){

                    $('#eca_max_people').val(data['students_enrolled'] + '/' + data['max_people'] + ' (Full)');

                }
                else {

                    $('#eca_max_people').val(data['students_enrolled'] + '/' + data['max_people']);

                }
                if (data['max_waiting_list'] == 0) {

                    $('#eca_max_waiting_list').val('N/A');
                }
                else {

                    $('#eca_max_waiting_list').val(data['students_in_waiting_list'] + '/' + data['max_waiting_list']);

                }
            }

        });
    }


});
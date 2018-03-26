var remove_symbol = $('.btn.btn-danger.btn-simple.btn-link');
var eca = window.location.href.split('/')[window.location.href.split('/').length - 1];
var first_item_waiting_list = $('#waiting_list tr:eq(1)')
var table_to_append = $('#students_enrolled tbody')

remove_symbol.click(function() {

    $.ajax({

                type: 'GET',
                url: '/eca/delete_student/' + eca + '/',
                timeout: 2000,
                dataType: 'json',
                data: 'id=' + this.id.split('-')[0] + '&action=' + this.id.split('-')[this.id.split('-').length - 1],
                success: function (data) {

                }

            });

            $('#' + this.id).parent().parent().fadeOut();



})

// Code to transfer from waiting list to enrolled list

$('#students_enrolled .btn.btn-danger.btn-simple.btn-link').click(function() {

    first_item_waiting_list.find('button:last').remove();
    first_item_waiting_list.appendTo(table_to_append).show('slow');
    first_item_waiting_list = $('#waiting_list tr:eq(1)')

})
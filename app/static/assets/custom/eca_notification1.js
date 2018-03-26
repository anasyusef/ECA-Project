var custom_status_notification = $('#custom_status_notification').parent();
var status_notification = $('#status_notification');

custom_status_notification.hide()

if (status_notification.val() == 'custom'){

        custom_status_notification.show();

    }
    else {

        custom_status_notification.hide();

    }

status_notification.on('change', function() {

    if (status_notification.val() == 'custom'){

        custom_status_notification.show()

    }
    else {

        custom_status_notification.hide()

    }


});
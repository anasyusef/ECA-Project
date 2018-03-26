$(document).ready(function() {
        $('.btn-simple.btn-link').click(function () {


            $.ajax({

                type: 'GET',
                url: '/record_attendance',
                timeout: 2000,
                dataType: 'json',
                data: 'eca=' + window.location.href.split('/')[window.location.href.split('/').length - 1] + '&attended=' + this.id,

            });

            $('#' + this.id).parent().parent().fadeOut();
            // Check if there are any <td> tags, since if there are not means that all the students are already registered for
            // attendance

            });

            if ($('td').length == 0) {
                $('.card-body').append("<div class=\"alert alert-info\">\n" +
                    "    <button type=\"button\" aria-hidden=\"true\" class=\"close\" data-dismiss=\"alert\">\n" +
                    "        <i class=\"nc-icon nc-simple-remove\"></i>\n" +
                    "    </button>\n" +
                    "    <span>All the users' attendance have been registered for today or there might be no students in this ECA, you may want to view the attendances instead</span>\n" +
                    "</div>")

            }

        });
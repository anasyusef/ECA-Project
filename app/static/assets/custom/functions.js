var student_username = document.getElementById('student_username');
var student_name = document.getElementById('student_first_name');
var student_last_name = document.getElementById('student_last_name');

    student_name.addEventListener('input', function() {
        student_username.value = student_name.value + '.' + student_last_name.value
    });
    student_last_name.addEventListener('input', function() {
        student_username.value = student_name.value + '.' + student_last_name.value
    });
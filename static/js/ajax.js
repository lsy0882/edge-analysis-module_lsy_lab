function ajax_get_status() {
    let state;
    $.ajax({
        type: 'GET',
        url: '/stats',
        dataType: 'JSON',
        async: false,
        success: function (result) {
            state = result;
        },
        error: function (xtr, status, error) {
            state = null;
        }
    });
    return state;
}

function ajax_run_module() {
    let state;
    $.ajax({
        type: 'GET',
        url: '/run_module',
        dataType: 'JSON',
        async: false,
        success: function (result) {
            state = result;
        },
        error: function (xtr, status, error) {
            state = null;
        }
    });
}

function ajax_get_settings() {
    let settings;
    $.ajax({
        type: 'GET',
        url: '/get_settings',
        dataType: 'JSON',
        async: false,
        success: function (result) {
            settings = result;
        },
        error: function (xtr, status, error) {
            settings = null;
        }
    });
    return settings;
}

function ajax_set_settings(settings) {
    let ret;
    $.ajax({
        type: 'POST',
        url: '/set_settings',
        dataType: 'JSON',
        data: settings,
        async: false,
        success: function (result) {
            ret = result;
            if (ret["ret"])
                alert("설정을 적용하였습니다.")
            else
                alert("설정 적용을 실패하였습니다.\n관리자에게 문의하십시오.")
        },
        error: function (xtr, status, error) {
            ret = null;
            alert("모듈에 에러가 발생하였습니다.\n관리자에게 문의하십시오.")
        }
    });
}

function ajax_run_task(){
    let ret;
    $.ajax({
        type: 'GET',
        url: '/run_task',
        dataType: 'JSON',
        async: false,
        success: function (result) {
            draw_task(result)
        },
        error: function (xtr, status, error) {
            ret = null;
        }
    });
}

function ajax_get_task(){
    let ret;
    $.ajax({
        type: 'GET',
        url: '/get_task',
        dataType: 'JSON',
        async: false,
        success: function (result) {
            ret = result;
        },
        error: function (xtr, status, error) {
            ret = null;
        }
    });
    return ret
}

function ajax_delete_task() {
    let ret;
    $.ajax({
        type: 'GET',
        url: '/delete_task',
        dataType: 'JSON',
        async: false,
        success: function (result) {
            ret = result;
            let task_id = "실행 중인 Task 없음"
            let task_type = "-"
            let task_state = "-"
            let task_start_time = "-"
            let task_elapsed_time = "-"

            document.getElementById("task-id").value = task_id;
            document.getElementById("task-type").value = task_type;
            document.getElementById("task-state").value = task_state;
            document.getElementById("task-start-time").value = task_start_time;
            document.getElementById("task-elapsed-time").value = task_elapsed_time;

            document.getElementById("btn-start-task").removeAttribute("disabled");
            document.getElementById("btn-delete-task").setAttribute("disabled","disabled");
        },
        error: function (xtr, status, error) {
            ret = null;
        }
    });
    return ret
}


function ajax_get_proxy_url() {
    let ret;
    $.ajax({
        type: 'GET',
        url: '/get_proxy_url',
        dataType: 'JSON',
        async: false,
        success: function (result) {
            let ret = result["ret"];
            let proxy_url = result["proxy_url"];
            let message = result["message"];
            if (ret) {
                document.getElementById("btn-play-proxy").removeAttribute("disabled");
                document.getElementById("btn-get-proxy").setAttribute("disabled","disabled");
            } else {
                alert(message)
            }
            document.getElementById("proxy-streaming-url").value = proxy_url;
        },
        error: function (xtr, status, error) {
            ret = null;
        }
    });
    return ret
}
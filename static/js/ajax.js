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
        async: true,
        success: function (result) {
            // ret = result;
            console.log(result)
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
}
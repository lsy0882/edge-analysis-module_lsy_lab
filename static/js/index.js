let cpu_color = "rgb(0, 153, 0)";
let mem_color = "rgb(240, 200, 0)";
let gpu_color = "rgb(102, 102, 255)";
let disk_color = "rgb(240, 140, 0)";
let height = 24;
let value = [Math.round(Math.random()*height)];
let event_names = ["assault", "falldown", "kidnapping", "tailing", "wanderer"];
let tracker_names = ["byte_tracker", "sort_tracker"]


function create_gage_bar(id, type) {
    let width, color;
    let height = 24;
    let width_cpu = 360;
    let width_mem = 360;
    let width_gpu = 442;
    let width_disk = 402;
    if (type==="cpu"){
        width = width_cpu;
        color = cpu_color;
    } else if (type==="mem"){
        width = width_mem;
        color = mem_color;
    } else if (type==="gpu"){
        width = width_gpu;
        color = gpu_color;
    } else {
        width = width_disk;
        color = disk_color;
    }

    let span = d3.select("#gage-" + id)
    let svg = span.append("svg")
        .attr("id", "gage-svg-" + id)
        .attr("height", height)
        .attr("width", width)
    let rect =  svg.selectAll("rect")
        .data(value)
        .enter()
        .append("rect")
        .attr("id", "rect-gage-" + id)
        .attr("x", 0)
        .attr("y", 0)
        .attr("width", 0)
        .attr("height", height)
        .attr("fill", color);
    let text = svg.append("text")
        .attr("id", "text-gage-" + id)
        .attr("x", width_cpu-30)
        .attr("y", height/2 + 5)
        .text("0%")
}

function draw_status() {
    let status = ajax_get_status();

    let cpu = status["CPU"];
    let cpu_usage = cpu["usage"];
    let cpu_clock = cpu["clock"];
    let height = 24;

    let width_cpu = 134;
    let width_mem = 134;
    let width_gpu = 430;
    let width_disk = 402;
    let base_padding = 40;
    let padding = 8;

    // CPU status
    for (let i = 0; i < cpu["usage"]["value"].length; i++) {
        let value = cpu_usage["value"][i];
        let usage = Math.round(value)/100 * width_cpu;
        let str_cpu_usage = cpu_usage["value"][i].toString();
        d3.select("#rect-gage-cpu-" + (i + 1))
            .transition()
            .attr("x", "0")
            .attr("width", usage)
            .attr("fill", cpu_color);
        d3.select("#text-gage-cpu-" + (i + 1))
            .attr("x", width_cpu - (padding * (str_cpu_usage.length - 1) + base_padding))
            .attr("y", height/2 + 5)
            .text(str_cpu_usage + cpu_usage["unit"]);
        d3.select("#clock-cpu-" + (i + 1)).text(cpu_clock["value"][i]);
        d3.select("#clock-unit-cpu-" + (i + 1)).text(cpu_clock["unit"]);
    }

    // Memory status
    let mem_type = ["RAM", "SWAP"]
    let mem_id = ["ram", "swap"]

    for (let i = 0; i < mem_type.length; i++) {
        let mem = status["MEM"][mem_type[i]];
        let mem_cur_value = mem["CUR"].toString();
        let mem_max_value = mem["MAX"].toString();
        let mem_usage = Math.round(mem_cur_value) / 10000 * width_mem;
        d3.select("#rect-gage-" + mem_id[i])
            .transition()
            .attr("x", "0")
            .attr("width", mem_usage)
            .attr("fill", mem_color);
        d3.select("#text-gage-" + mem_id[i])
            .attr("x", width_cpu - (padding * (mem_cur_value.length - 1) + base_padding + 10))
            .attr("y", height / 2 + 5)
            .text(mem_cur_value + status["MEM"]["unit"]);
        d3.select("#value-" + mem_id[i]).text(mem_cur_value + "/" + mem_max_value + status["MEM"]["unit"]);
    }

    // GPU status
    let gpu = status["GPU"];
    let gpu_usage = gpu["usage"];
    let gpu_clock = gpu["clock"];
    let value = gpu_usage["value"];
    let gpu_estimate_usage = Math.round(value)/100 * width_gpu;
    let str_gpu_usage = gpu_usage["value"].toString();

    d3.select("#rect-gage-gpu")
        .transition()
        .attr("x", "0")
        .attr("width", gpu_estimate_usage)
        .attr("fill", gpu_color);
    d3.select("#text-gage-gpu")
        .attr("x", width_gpu - (padding * (str_gpu_usage.length - 1) + base_padding))
        .attr("y", height/2 + 5)
        .text(str_gpu_usage + gpu_usage["unit"]);
    d3.select("#clock-gpu").text(gpu_clock["value"]);
    d3.select("#clock-unit-gpu").text(gpu_clock["unit"]);


    // Disk status
    let disk_type = ["main", "external"]
    let disk_id = ["main-disk", "external-disk"]
    for (let i = 0; i < disk_type.length; i++) {
        let disk = status["DISK"][disk_type[i]];
        let disk_used_value = Math.round(disk["used"]).toString();
        let disk_total_value = Math.round(disk["total"]).toString();
        let disk_usage = Math.round(disk_used_value) / disk_total_value * width_disk;
        d3.select("#rect-gage-" + disk_id[i])
            .transition()
            .attr("x", "0")
            .attr("width", disk_usage)
            .attr("fill", disk_color);
        d3.select("#text-gage-" + disk_id[i])
            .attr("x", width_disk - (padding * (disk_used_value.length - 1) + base_padding))
            .attr("y", height / 2 + 5)
            .text(disk_used_value + disk["unit"]);
        d3.select("#value-" + disk_id[i]).text(disk_used_value + "/" + disk_total_value + disk["unit"]);
    }

    // Temp status
    let temp_type = ["CPU","GPU", "DEVICE"];
    let temp_id = ["cpu","gpu", "device"];

    for (let i = 0; i < temp_type.length; i++) {
        let temp = status["TEMP"];
        d3.select("#temp-" + temp_id[i]).text(temp[temp_type[i]]);
        d3.select("#temp-unit-" + temp_id[i]).text(temp["unit"]);
    }

    // Power status
    let power_type = ["TOTAL","CPU GPU CV", "SOC"];
    let power_id = ["total","cpugpucv", "soc"];

    for (let i = 0; i < power_type.length; i++) {
        let power = status["POWER"];
        d3.select("#power-" + power_id[i]).text(power[power_type[i]]);
        d3.select("#power-unit-" + power_id[i]).text(power["unit"]);
    }
}

function draw_settings() {
    let settings = ajax_get_settings()["settings"];
    let cctv_info = settings["cctv_info"];
    let communication_info = settings["communication_info"];
    let decode_option = settings["decode_option"];
    let model_option = settings["model"];

    // CCTV info
    let streaming_url = cctv_info["streaming_url"];
    let cam_id = cctv_info["cam_id"];
    let cctv_type = "";
    if (cctv_info["streaming_type"] === "cctv")
        cctv_type = "0";
    else
        cctv_type = "1";
    // TODO: get proxy url

    // Archive module
    let archive_module_ip = communication_info["server_url"]["ip"]
    let archive_module_port = communication_info["server_url"]["port"]

    // Decoding option
    let decoding_fps = decode_option["fps"].toString();

    // Object detection model option
    let object_detection_model_option = model_option["object_detection"];
    let model_name      = object_detection_model_option["model_name"];
    let score_threshold = object_detection_model_option["score_threshold"];
    let nms_threshold   = object_detection_model_option["nms_threshold"];

    // Tracker option
    let tracker_option = model_option["tracker"];
    let selected_tracker_names = tracker_option["tracker_names"];
    let byte_tracker_option = tracker_option["byte_tracker"];
    let byte_tracker_score_threshold = byte_tracker_option["score_threshold"];
    let byte_tracker_track_threshold = byte_tracker_option["track_threshold"];
    let byte_tracker_track_buffer = byte_tracker_option["track_buffer"];
    let byte_tracker_match_threshold = byte_tracker_option["match_threshold"];
    let byte_tracker_min_box_area = byte_tracker_option["min_box_area"];
    let byte_tracker_frame_rate = byte_tracker_option["frame_rate"];
    let sort_tracker_option = tracker_option["sort_tracker"];
    let sort_tracker_score_threshold = sort_tracker_option["score_threshold"];
    let sort_tracker_max_age = sort_tracker_option["max_age"];
    let sort_tracker_min_hits = sort_tracker_option["min_hits"];

    // Event detection model option
    let event_model = model_option["event"];
    let selected_event_names = event_model["event_names"];
    let event_options = event_model["event_options"]
    let assault_score_threshold = event_options["assault"]["score_threshold"]
    let assault_tracker = event_options["assault"]["tracker"]
    let falldown_score_threshold = event_options["falldown"]["score_threshold"]
    let falldown_tracker = event_options["falldown"]["tracker"]
    let kidnapping_score_threshold = event_options["kidnapping"]["score_threshold"]
    let kidnapping_tracker = event_options["kidnapping"]["tracker"]
    let tailing_score_threshold = event_options["tailing"]["score_threshold"]
    let tailing_tracker = event_options["tailing"]["tracker"]
    let wanderer_score_threshold = event_options["wanderer"]["score_threshold"]
    let wanderer_tracker = event_options["wanderer"]["tracker"]

    // Set values in UI
    document.getElementById("input-streaming-url").value = streaming_url;
    $("#select-cam-id").val(cam_id).prop("selected", true);
    $("#select-cctv-type").val(cctv_type).prop("selected", true);
    document.getElementById("archive-module-ip").value = archive_module_ip;
    document.getElementById("archive-module-port").value = archive_module_port;
    $("#select-decoding-fps").val(decoding_fps).prop("selected", true);
    $("#select-od-model-name").val(model_name).prop("selected", true);
    $("#select-od-score-threshold").val(score_threshold).prop("selected", true);
    $("#select-od-nms-threshold").val(nms_threshold).prop("selected", true);
    $("#select-byte-tracker-score-threshold").val(byte_tracker_score_threshold).prop("selected", true);
    $("#select-byte-tracker-track-threshold").val(byte_tracker_track_threshold).prop("selected", true);
    $("#select-byte-tracker-track-buffer").val(byte_tracker_track_buffer).prop("selected", true);
    $("#select-byte-tracker-match-threshold").val(byte_tracker_match_threshold).prop("selected", true);
    $("#select-byte-tracker-min-box-area").val(byte_tracker_min_box_area).prop("selected", true);
    $("#select-byte-tracker-frame-rate").val(byte_tracker_frame_rate).prop("selected", true);
    $("#select-sort-tracker-score-threshold").val(sort_tracker_score_threshold).prop("selected", true);
    $("#select-sort-tracker-max-age").val(sort_tracker_max_age).prop("selected", true);
    $("#select-sort-tracker-min-hits").val(sort_tracker_min_hits).prop("selected", true);

    for (let i = 0; i < tracker_names.length; i++) {
        if (selected_tracker_names.includes(tracker_names[i])) {
            $("#checkbox-" + tracker_names[i]).prop("checked", true)
            $("#collapse-" + tracker_names[i]).prop("class", "collapse show")
        }
    }
    for (let i = 0; i < event_names.length; i++) {
        if (selected_event_names.includes(event_names[i])) {
            $("#checkbox-" + event_names[i]).prop("checked", true)
            $("#collapse-" + event_names[i]).prop("class", "collapse show")
        }
    }
    $("#select-assault-score-threshold").val(assault_score_threshold).prop("selected", true);
    $("#select-assault-tracker").val(assault_tracker).prop("selected", true);
    $("#select-falldown-score-threshold").val(falldown_score_threshold).prop("selected", true);
    $("#select-falldown-tracker").val(falldown_tracker).prop("selected", true);
    $("#select-kidnapping-score-threshold").val(kidnapping_score_threshold).prop("selected", true);
    $("#select-kidnapping-tracker").val(kidnapping_tracker).prop("selected", true);
    $("#select-tailing-score-threshold").val(tailing_score_threshold).prop("selected", true);
    $("#select-tailing-tracker").val(tailing_tracker).prop("selected", true);
    $("#select-wanderer-score-threshold").val(wanderer_score_threshold).prop("selected", true);
    $("#select-wanderer-tracker").val(wanderer_tracker).prop("selected", true);
}

function save_settings() {
    let cctv_types = ["cctv", "test"]

    let input_streaming_url = document.getElementById("input-streaming-url");
    let select_cctv_type = document.getElementById("select-cctv-type");
    let select_cam_id = document.getElementById("select-cam-id")
    let input_archive_module_ip = document.getElementById("archive-module-ip");
    let input_archive_module_port = document.getElementById("archive-module-port");
    let select_decoding_fps = document.getElementById("select-decoding-fps");
    // object detection option
    let select_od_model_name = document.getElementById("select-od-model-name");
    let select_od_score_threshold = document.getElementById("select-od-score-threshold");
    let select_od_nms_threshold = document.getElementById("select-od-nms-threshold");
    // tracker option
    let select_byte_tracker_score_threshold = document.getElementById("select-byte-tracker-score-threshold");
    let select_byte_tracker_track_threshold = document.getElementById("select-byte-tracker-track-threshold");
    let select_byte_tracker_track_buffer = document.getElementById("select-byte-tracker-track-buffer");
    let select_byte_tracker_match_threshold = document.getElementById("select-byte-tracker-match-threshold");
    let select_byte_tracker_min_box_area = document.getElementById("select-byte-tracker-min-box-area");
    let select_byte_tracker_frame_rate = document.getElementById("select-byte-tracker-frame-rate");
    let select_sort_tracker_score_threshold = document.getElementById("select-sort-tracker-score-threshold");
    let select_sort_tracker_max_age = document.getElementById("select-sort-tracker-max-age");
    let select_sort_tracker_min_hits = document.getElementById("select-sort-tracker-min-hits");
    // event detection option = document.getElementById("");
    let select_assault_score_threshold = document.getElementById("select-assault-score-threshold");
    let select_assault_tracker = document.getElementById("select-assault-tracker");
    let select_falldown_score_threshold = document.getElementById("select-falldown-score-threshold");
    let select_falldown_tracker = document.getElementById("select-falldown-tracker");
    let select_kidnapping_score_threshold = document.getElementById("select-kidnapping-score-threshold");
    let select_kidnapping_tracker = document.getElementById("select-kidnapping-tracker");
    let select_tailing_score_threshold = document.getElementById("select-tailing-score-threshold");
    let select_tailing_tracker = document.getElementById("select-tailing-tracker");
    let select_wanderer_score_threshold = document.getElementById("select-wanderer-score-threshold");
    let select_wanderer_tracker = document.getElementById("select-wanderer-tracker");

    let streaming_url = input_streaming_url.value;
    let streaming_type = cctv_types[select_cctv_type.options[select_cctv_type.selectedIndex].value];
    let cam_id = select_cam_id.options[select_cam_id.selectedIndex].value;
    let archive_module_ip = input_archive_module_ip.value;
    let archive_module_port = input_archive_module_port.value;
    let decoding_fps = select_decoding_fps.options[select_decoding_fps.selectedIndex].value;
    let od_model_name = select_od_model_name.options[select_od_model_name.selectedIndex].value;
    let od_score_threshold = select_od_score_threshold.options[select_od_score_threshold.selectedIndex].value;
    let od_nms_threshold = select_od_nms_threshold.options[select_od_nms_threshold.selectedIndex].value;

    let checked_tracker_names = "";
    for (let i = 0; i < tracker_names.length; i++) {
        if ($("#checkbox-" + tracker_names[i]).prop("checked")) {
            if (i === tracker_names.length - 1)
                checked_tracker_names += tracker_names[i];
            else
                checked_tracker_names += (tracker_names[i] + ",");
        }
    }

    let checked_event_names = "";
    for (let i = 0; i < event_names.length; i++) {
        if ($("#checkbox-" + event_names[i]).prop("checked")) {
            if (i === event_names.length - 1)
                checked_event_names += event_names[i];
            else
                checked_event_names += (event_names[i] + ",");
        }
    }
    let byte_tracker_score_threshold = select_byte_tracker_score_threshold.options[select_byte_tracker_score_threshold.selectedIndex].value;
    let byte_tracker_track_threshold = select_byte_tracker_track_threshold.options[select_byte_tracker_track_threshold.selectedIndex].value;
    let byte_tracker_track_buffer = select_byte_tracker_track_buffer.options[select_byte_tracker_track_buffer.selectedIndex].value;
    let byte_tracker_match_threshold = select_byte_tracker_match_threshold.options[select_byte_tracker_match_threshold.selectedIndex].value;
    let byte_tracker_min_box_area = select_byte_tracker_min_box_area.options[select_byte_tracker_min_box_area.selectedIndex].value;
    let byte_tracker_frame_rate = select_byte_tracker_frame_rate.options[select_byte_tracker_frame_rate.selectedIndex].value;
    let sort_tracker_score_threshold = select_sort_tracker_score_threshold.options[select_sort_tracker_score_threshold.selectedIndex].value;
    let sort_tracker_max_age = select_sort_tracker_max_age.options[select_sort_tracker_max_age.selectedIndex].value;
    let sort_tracker_min_hits = select_sort_tracker_min_hits.options[select_sort_tracker_min_hits.selectedIndex].value;
    let assault_score_threshold = select_assault_score_threshold.options[select_assault_score_threshold.selectedIndex].value;
    let assault_tracker = select_assault_tracker.options[select_assault_tracker.selectedIndex].value;
    let falldown_score_threshold = select_falldown_score_threshold.options[select_falldown_score_threshold.selectedIndex].value;
    let falldown_tracker = select_falldown_tracker.options[select_falldown_tracker.selectedIndex].value;
    let kidnapping_score_threshold = select_kidnapping_score_threshold.options[select_kidnapping_score_threshold.selectedIndex].value;
    let kidnapping_tracker = select_kidnapping_tracker.options[select_kidnapping_tracker.selectedIndex].value;
    let tailing_score_threshold = select_tailing_score_threshold.options[select_tailing_score_threshold.selectedIndex].value;
    let tailing_tracker = select_tailing_tracker.options[select_tailing_tracker.selectedIndex].value;
    let wanderer_score_threshold = select_wanderer_score_threshold.options[select_wanderer_score_threshold.selectedIndex].value;
    let wanderer_tracker = select_wanderer_tracker.options[select_wanderer_tracker.selectedIndex].value;

    let settings = {
        "streaming_url": streaming_url,
        "streaming_type": streaming_type,
        "cam_id": cam_id,
        "archive_server_ip": archive_module_ip,
        "archive_server_port": archive_module_port,
        "decode_fps": parseInt(decoding_fps),
        "od_model_name": od_model_name,
        "od_score_threshold": parseFloat(od_score_threshold),
        "od_nms_threshold": parseFloat(od_nms_threshold),
        "tracker_names": checked_tracker_names,
        "byte_tracker_score_threshold": byte_tracker_score_threshold,
        "byte_tracker_track_threshold": byte_tracker_track_threshold,
        "byte_tracker_track_buffer": byte_tracker_track_buffer,
        "byte_tracker_match_threshold": byte_tracker_match_threshold,
        "byte_tracker_min_box_area": byte_tracker_min_box_area,
        "byte_tracker_frame_rate": byte_tracker_frame_rate,
        "sort_tracker_score_threshold": sort_tracker_score_threshold,
        "sort_tracker_max_age": sort_tracker_max_age,
        "sort_tracker_min_hits": sort_tracker_min_hits,
        "event_names": checked_event_names,
        "assault_score_threshold": assault_score_threshold,
        "assault_tracker": assault_tracker,
        "falldown_score_threshold": falldown_score_threshold,
        "falldown_tracker": falldown_tracker,
        "kidnapping_score_threshold": kidnapping_score_threshold,
        "kidnapping_tracker": kidnapping_tracker,
        "tailing_score_threshold": tailing_score_threshold,
        "tailing_tracker": tailing_tracker,
        "wanderer_score_threshold": wanderer_score_threshold,
        "wanderer_tracker": wanderer_tracker,
    }
    ajax_set_settings(settings);
}

function draw_task(task) {
    let result = task;
    if (result  === null)
        result = ajax_get_task();

    let task_id = "실행 중인 Task 없음"
    let task_type = "-"
    let task_state = "-"
    let task_start_time = "-"
    let task_elapsed_time = "-"

    let task_ret = result["ret"]
    if (task_ret) {
        task_id = result["id"];
        task_type = result["type"];
        task_state = result["state"];
        task_start_time = result["start_time"];
        task_elapsed_time = result["start_time_num"]

        let elapsed_time = Math.abs(new Date() - task_elapsed_time*1000);
        task_elapsed_time = ms2strtime(parseInt(elapsed_time));
        document.getElementById("btn-start-task").setAttribute("disabled","disabled");
        document.getElementById("btn-delete-task").removeAttribute("disabled");
    }
    else {
        document.getElementById("btn-start-task").removeAttribute("disabled");
        document.getElementById("btn-delete-task").setAttribute("disabled","disabled");
    }

    document.getElementById("task-id").value = task_id;
    document.getElementById("task-type").value = task_type;
    document.getElementById("task-state").value = task_state;
    document.getElementById("task-start-time").value = task_start_time;
    document.getElementById("task-elapsed-time").value = task_elapsed_time;
}

function ms2strtime(ms) {
    let seconds = ms / 1000;
    const hours = parseInt( seconds / 3600 ); // 3,600 seconds in 1 hour
    seconds = seconds % 3600; // seconds remaining after extracting hours
    const minutes = parseInt( seconds / 60 ); // 60 seconds in 1 minute
    seconds = parseInt(seconds % 60);
    return String(hours).padStart(2, "0") + "시간 "+ String(minutes).padStart(2, "0") + "분 " + String(seconds).padStart(2, "0") + "초";
}

function play_proxy() {
    let proxy_url = document.getElementById("proxy-streaming-url").value;
    play_url("video", proxy_url);
    document.getElementById("btn-play-proxy").setAttribute("disabled","disabled");
}
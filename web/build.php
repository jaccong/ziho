<?php
// ziho 接口预计算：从 all_history.json 生成 api/*.json
// 由 save.php 在数据同步成功后调用；也可手动访问 build.php 触发
if (!headers_sent()) header("Content-Type: text/plain; charset=utf-8");

$base = __DIR__;
$src = $base . "/all_history.json";
$outDir = $base . "/api";

if (!file_exists($src)) { echo "fail: all_history.json not found"; exit; }
$raw = json_decode(file_get_contents($src), true);
if (!$raw || empty($raw["days"])) { echo "fail: bad json"; exit; }

$days = $raw["days"];
usort($days, function($a, $b){ return strcmp($a["date"], $b["date"]); });
if (!is_dir($outDir)) mkdir($outDir, 0755, true);

// ---- days.json ----
$dayList = [];
foreach ($days as $d) {
    $lbDist = []; $shouban = 0; $lianbanN = 0; $maxLb = 0;
    foreach ($d["stocks"] as $s) {
        $lb = (int)$s["lianban"];
        $k = (string)$lb;
        $lbDist[$k] = ($lbDist[$k] ?? 0) + 1;
        if ($lb > $maxLb) $maxLb = $lb;
        if ($lb <= 1) $shouban++; else $lianbanN++;
    }
    $dayList[] = [
        "date" => $d["date"],
        "total" => count($d["stocks"]),
        "shouban" => $shouban,
        "lianban" => $lianbanN,
        "max_lb" => $maxLb,
        "lb_dist" => $lbDist,
    ];
}

// ---- stocks.json ----
$cnt = []; $maxlb = []; $first = []; $last = []; $secs = []; $names = [];
foreach ($days as $d) {
    foreach ($d["stocks"] as $s) {
        $c = $s["code"];
        $cnt[$c] = ($cnt[$c] ?? 0) + 1;
        $names[$c] = $s["name"];
        $lb = (int)$s["lianban"];
        if (!isset($maxlb[$c]) || $lb > $maxlb[$c]) $maxlb[$c] = $lb;
        if (!isset($first[$c])) $first[$c] = $d["date"];
        $last[$c] = $d["date"];
        $sec = $s["sector"] ?? "未知";
        $secs[$c][$sec] = true;
    }
}
$stocks = [];
foreach ($cnt as $c => $n) {
    $secList = array_keys($secs[$c]); sort($secList);
    $stocks[] = [
        "code" => $c, "name" => $names[$c], "count" => $n,
        "max_lb" => $maxlb[$c], "first" => $first[$c], "last" => $last[$c],
        "sectors" => $secList,
    ];
}
usort($stocks, function($a, $b){
    if ($a["count"] !== $b["count"]) return $b["count"] - $a["count"];
    return $b["max_lb"] - $a["max_lb"];
});

// ---- latest.json ----
$latestDay = $days[count($days) - 1];
$secCnt = [];
foreach ($latestDay["stocks"] as $s) {
    $sec = $s["sector"] ?? "未知";
    $secCnt[$sec] = ($secCnt[$sec] ?? 0) + 1;
}
arsort($secCnt);
$sectorsTop = [];
$i = 0;
foreach ($secCnt as $k => $v) {
    $sectorsTop[] = ["sector" => $k, "count" => $v];
    if (++$i >= 15) break;
}
$latest = [
    "date" => $latestDay["date"],
    "summary" => $dayList[count($dayList) - 1],
    "sectors_top" => $sectorsTop,
    "stocks" => $latestDay["stocks"],
];

// ---- meta.json ----
$meta = [
    "updated_at" => $latestDay["date"],
    "total_days" => count($days),
    "date_range" => [$days[0]["date"], $latestDay["date"]],
    "total_stocks" => count($stocks),
    "built_at" => date("Y-m-d H:i:s"),
];

$files = [
    "days.json" => $dayList,
    "stocks.json" => $stocks,
    "latest.json" => $latest,
    "meta.json" => $meta,
];
foreach ($files as $name => $data) {
    file_put_contents($outDir . "/" . $name,
        json_encode($data, JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES));
    echo "ok: $name\n";
}
// ---- day/{date}.json ----
$dayDir = $outDir . "/day";
if (!is_dir($dayDir)) mkdir($dayDir, 0755, true);
$summaries = [];
foreach ($dayList as $s) $summaries[$s["date"]] = $s;
foreach ($days as $d) {
    $one = ["date" => $d["date"], "summary" => $summaries[$d["date"]], "stocks" => $d["stocks"]];
    file_put_contents($dayDir . "/" . $d["date"] . ".json",
        json_encode($one, JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES));
}
echo "ok: day/*.json (" . count($days) . " files)\n";
echo "done\n";

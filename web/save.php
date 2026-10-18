<?php
// GitHub 原始JSON地址
$jsonUrl = "https://raw.githubusercontent.com/jaccong/ziho/main/all_history.json";
// 保存到虚拟主机的路径
$savePath = "./all_history.json";

// 拉取GitHub JSON
$opts = [
    'http' => [
        'timeout' => 60,
        'user_agent' => 'Mozilla/5.0'
    ]
];
$context = stream_context_create($opts);
$jsonContent = file_get_contents($jsonUrl, false, $context);

if ($jsonContent !== false) {
    file_put_contents($savePath, $jsonContent);
    echo "success: pulled " . strlen($jsonContent) . " bytes\n";
    // 数据更新后重建预计算接口
    if (file_exists(__DIR__ . "/build.php")) {
        echo "--- rebuild api ---\n";
        include __DIR__ . "/build.php";
    }
} else {
    echo "fail";
}
?>

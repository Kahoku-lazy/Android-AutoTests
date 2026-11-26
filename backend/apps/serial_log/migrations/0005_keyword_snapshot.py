from django.db import migrations

SNAPSHOT = [
    ('switch_on', 0, '设备开关', '打开设备成功'),
    ('switch_off', 1, '设备开关', '关闭设备成功'),
    ('color_configs_set_success', 2, '灯效库', '设置颜色成功'),
    ('color_configs_set_success', 17, '颜色模式', '分段-颜色设置成功'),
    ('timer_configs_set_success', 3, '定时功能', '设置预约定时成功'),
    ('awaken_configs_set_success', 4, '定时功能', '设置唤醒定时成功'),
    ('sleep_configs_set_success', 5, '定时功能', '设置睡眠定时成功'),
    ('lumi_set_success', 6, '亮度', '成功设置相对亮度'),
    ('music_mode_start', 7, '音乐模式', '成功切换到音乐模式'),
    ('music_mode_start', 8, '音乐模式', '设置为设备拾音'),
    ('phone_music_start', 9, '音乐模式', '设置为手机拾音'),
    ('music_mode_agile_sensitivity', 10, '音乐模式', '成功设置灵敏度'),
    ('music_configs_set_success', 11, '音乐模式', '音乐模式场景设置成功'),
    ('color_mode_start', 12, '颜色模式', '成功切换到颜色模式'),
    ('color_mode_start', 13, '颜色模式', '设置为分段'),
    ('color_gradient_open_success', 14, '颜色模式', '分段-渐变开启'),
    ('color_gradient_close_success', 15, '颜色模式', '分段-渐变关闭'),
    ('set_color_segment_lumi_success', 16, '颜色模式', '分段-相对亮度设置成功'),
    ('gra_mode_start', 18, '颜色模式', '设置为高阶'),
    ('graffiti_configs_set_success', 19, '颜色模式', '高阶模式下-颜色设置成功'),
    ('abstract_mode_start', 20, '场景模式', '成功切换至场景模式'),
    ('scene_configs_set_success', 21, '场景模式', '灯效场景设置成功'),
    ('diy_mode_start', 22, 'DIY模式', '成功切换至DIY模式'),
    ('diy_configs_set_success', 23, 'DIY模式', 'DIY灯效设置成功'),
    ('video_mode_start', 24, '视频模式', '成功切换至视频模式'),
    ('video_config_success', 25, '视频模式', '视频模式设置成功'),
    ('set_color_video_lumi_success', 26, '视频模式', '相对亮度'),
    ('set_video_color_calibration_success', 27, '视频模式', '颜色校准'),
    ('set_video_game_success', 28, '视频模式', '游戏/戏剧'),
    ('set_video_drama_success', 28, '视频模式', '游戏/戏剧'),
    ('set_video_segment_success', 29, '视频模式', '分段/整段'),
    ('set_video_all_segment_success', 29, '视频模式', '分段/整段'),
    ('video_sound_effect_open', 30, '视频模式', '声音效果'),
    ('video_sound_effect_close', 30, '视频模式', '声音效果'),
    ('video_black_edge_elimination_open', 31, '视频模式', '黑边消除'),
    ('video_black_edge_elimination_close', 31, '视频模式', '黑边消除'),
    ('video_black_screen_setting_open', 32, '视频模式', '黑屏设置'),
    ('video_black_screen_setting_close', 32, '视频模式', '黑屏设置'),
    ('music_dreamview_mode_start', 33, '音乐盛宴', '切换到音乐盛宴'),
    ('music_dreamview_configs_success', 34, '音乐盛宴', '音乐盛宴设置成功'),
    ('music_dreamview_open', 35, '音乐盛宴', '音乐盛宴开关'),
    ('music_dreamview_close', 35, '音乐盛宴', '音乐盛宴开关'),
    ('music_dreamview_lumi_unify_open', 36, '音乐盛宴', '亮度统一'),
    ('music_dreamview_lumi_unify_close', 36, '音乐盛宴', '亮度统一'),
    ('set_music_dreamview_lumi_success', 37, '音乐盛宴', '亮度'),
    ('set_music_dreamview_sensitivity_success', 38, '音乐盛宴', '灵敏度'),
    ('set_music_dreamview_scene_success', 39, '音乐盛宴', '场景选择'),
    ('set_music_dreamview_model_dongan', 40, '音乐盛宴', '动感/柔和'),
    ('set_music_dreamview_model_ronghe', 40, '音乐盛宴', '动感/柔和'),
    ('viewing_dreamview_mode_start', 41, '观影盛宴', '切换到观影盛宴'),
    ('viewing_dreamview_configs_success', 42, '观影盛宴', '观影盛宴设置成功'),
    ('viewing_dreamview_open', 43, '观影盛宴', '观影盛宴开关'),
    ('viewing_dreamview_close', 43, '观影盛宴', '观影盛宴开关'),
    ('viewing_dreamview_lumi_unify_open', 44, '观影盛宴', '亮度统一'),
    ('viewing_dreamview_lumi_unify_close', 44, '观影盛宴', '亮度统一'),
    ('set_viewing_dreamview_lumi_success', 45, '观影盛宴', '亮度'),
    ('set_viewing_dreamview_saturability_success', 46, '观影盛宴', '饱和度'),
    ('set_viewing_dreamview_game_success', 47, '观影盛宴', '游戏/戏剧'),
    ('set_viewing_dreamview_drama_success', 47, '观影盛宴', '游戏/戏剧'),
    ('set_viewing_dreamview_segment_success', 48, '观影盛宴', '分段/整段'),
    ('set_viewing_dreamview_all_segment_success', 48, '观影盛宴', '分段/整段'),
    ('viewing_dreamview_video_sound_effect_open', 49, '观影盛宴', '声音效果'),
    ('viewing_dreamview_video_sound_effect_close', 49, '观影盛宴', '声音效果'),
    ('abstract_dreamview_mode_start', 50, '场景盛宴', '切换到场景盛宴'),
    ('abstract_dreamview_configs_success', 51, '场景盛宴', '场景盛宴设置成功'),
    ('abstract_dreamview_lumi_unify_open', 52, '场景盛宴', '亮度统一'),
    ('abstract_dreamview_lumi_unify_close', 52, '场景盛宴', '亮度统一'),
    ('set_abstract_dreamview_lumi_success', 53, '场景盛宴', '亮度'),
    ('set_abstract_dreamview_sound_phone_success', 54, '场景盛宴', '声音播放-手机'),
    ('set_abstract_dreamview_scene_success', 55, '场景盛宴', '场景选择'),
]


def forwards(apps, schema_editor):
    LogKeyword = apps.get_model("serial_log", "LogKeyword")
    for index, (keyword, feature_id, module, feature) in enumerate(SNAPSHOT):
        LogKeyword.objects.get_or_create(
            keyword=keyword,
            feature_id=feature_id,
            scope="*",
            defaults={"module": module, "feature": feature, "sort_order": (index + 1) * 10},
        )


def backwards(apps, schema_editor):
    LogKeyword = apps.get_model("serial_log", "LogKeyword")
    LogKeyword.objects.all().delete()


class Migration(migrations.Migration):
    dependencies = [
        ("serial_log", "0004_logkeyword"),
    ]

    operations = [
        migrations.RunPython(forwards, backwards),
    ]

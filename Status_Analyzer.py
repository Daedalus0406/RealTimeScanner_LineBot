import datetime
import line_notify as ln


# 製程階段判斷
# 製程開始/抽真空
def status_analyzer(filtered_df, flag, time_in, vpi_ad):
    time_out = 2
    message = " "
    df_len = len(filtered_df.index) - 1
    # print(filtered_df)

    for i, ds_temp in filtered_df.iterrows():
        if i + 1 <= df_len:
            ds_temp_next = filtered_df.loc[i + 1, ["time", "infusion_pressure", "infusion_vacuum", "vac_status",
                                                   "pre_status"]]
            # print(ds_temp)
            if flag == 0:
                if flag == 0 and ds_temp['vac_status'] == 2 and ds_temp_next['vac_status'] == 1:  # 製程開始
                    status = "製程開始"
                    flag = 1
                    time_out = 2

                elif ds_temp['vac_status'] == 1 and ds_temp_next['vac_status'] == 1:  # 抽真空
                    status = "抽真空中"
                    time_out = time_in + 1
                    flag = 1

                elif ds_temp['vac_status'] == 0 and ds_temp_next['vac_status'] == 0:  # 真空維持
                    status = "真空維持中"
                    flag = 2

                elif ds_temp['pre_status'] == 0 and ds_temp_next['pre_status'] > ds_temp['pre_status']:  # 加壓開始
                    status = "加壓開始"
                    flag = 3

                elif ds_temp['pre_status'] >= 1 and ds_temp_next['pre_status'] < 3 and ds_temp_next['infusion_pressure'] - ds_temp['infusion_pressure'] > 0.01:
                    status = "加壓中"
                    time_out = time_in + 1
                    flag = 3

                elif ds_temp['pre_status'] == 3:  # 加壓維持
                    status = "加壓維持"
                    flag = 4

                elif ds_temp['pre_status'] == 3 and ds_temp_next['pre_status'] == 2 and ds_temp['infusion_pressure'] > ds_temp_next['infusion_pressure']:  # 第一次洩壓
                    status = "初次洩壓"
                    flag = 5

                elif ds_temp_next['pre_status'] == 2 and ds_temp['infusion_pressure'] > ds_temp_next['infusion_pressure']:  # 洩壓中
                    status = "洩壓中"
                    flag = 5

                elif ds_temp['pre_status'] == 2 and ds_temp_next['pre_status'] == 1:  # 完全洩壓/製程結束
                    status = "製程結束"
                    flag = 6

                elif ds_temp['pre_status'] <= 1 and ds_temp['vac_status'] == 2:
                    status = "待機中"
                    flag = 0

            elif flag == 1 and ds_temp['vac_status'] == 1 and ds_temp_next['vac_status'] == 1:
                if time_in <= 30:
                    status = "抽真空中"
                    time_out = time_in + 1
                    flag = 1

                else:
                    message = "即時異常警告\n含浸爐" + vpi_ad + "\n抽真空異常: 已超出規範時間\n規範時間: 30分鐘\n目前壓力值: " + \
                              str(ds_temp['infusion_pressure'])[:3] + " kg/cm^2\n目前真空值: " + str(ds_temp['infusion_vacuum'])[:3] + " torr"
                    status = message

                    time_out = time_in + 1
                    flag = 1

            # 真空維持
            elif flag == 1 and ds_temp['vac_status'] == 1 and ds_temp_next['vac_status'] == 0:
                status = "抽真空結束"
                flag = 2
                time_out = 2

            elif flag == 2 and ds_temp['pre_status'] == 0 and ds_temp_next['pre_status'] == 0:
                if ds_temp['infusion_vacuum'] <= 5:
                    status = "真空維持中"
                    flag = 2

                elif ds_temp['infusion_vacuum'] > 5:  # 如果真空度超過< 5 torr >十分鐘以上發布警報
                    if time_in <= 10:
                        status = vpi_ad + "真空值超出標準值"
                        time_out = time_in + 1
                        flag = 2
                    else:
                        message = "即時異常警告\n含浸爐" + vpi_ad + "\n真空維持異常: 真空值超出標準值\n規範真空值: 5 torr\n目前壓力值: " + \
                              str(ds_temp['infusion_pressure'])[:3] + " kg/cm^2\n目前真空值: " + str(ds_temp['infusion_vacuum'])[:3] + " torr"
                        status = message
                        # ln.line_notify(message, time_in)
                        time_out = time_in + 1
                        flag = 2

            # 加壓開始
            elif flag == 2 and ds_temp['pre_status'] == 0 and ds_temp_next['pre_status'] == 1:
                status = "加壓開始"
                time_out = 2
                flag = 3

            elif flag == 3 and ds_temp['pre_status'] >= 1 and ds_temp_next['pre_status'] < 3:
                if time_in <= 90:
                    status = "加壓中"
                    time_out = time_in + 1
                    flag = 3

                elif time_in > 90:
                    message = "即時異常警告\n含浸爐" + vpi_ad + "\n加壓異常: 超出規範時間\n規範時間: 90分鐘\n目前壓力值: " + \
                              str(ds_temp['infusion_pressure'])[:3] + " kg/cm^2\n目前真空值: " + str(ds_temp['infusion_vacuum'])[:3] + " torr"
                    status = message
                    # ln.line_notify(message, time_in)
                    time_out = time_in + 1
                    flag = 3

            # 加壓維持
            elif flag == 3 and ds_temp['infusion_pressure'] <= 6 and ds_temp_next['infusion_pressure'] >= 6:
                status = "加壓維持開始"
                time_out = 2
                flag = 4

            elif flag == 4 and ds_temp['infusion_pressure'] >= 6:
                status = "加壓維持"
                flag = 4

            # 壓力值小於6kg/cm^2時
            elif flag == 4 and ds_temp['infusion_pressure'] < 6:
                if time_in < 10 and ds_temp['infusion_pressure'] > 3:
                    status = vpi_ad + "壓力值低於加壓標準值"
                    time_out = time_in + 1
                    flag = 4

                elif time_in <= 10 and ds_temp['infusion_pressure'] <= 3:
                    status = "初次洩壓結束"
                    time_out = 2
                    flag = 5

                else:
                    message = "即時異常警告\n含浸爐" + vpi_ad + "\n壓力維持異常: 壓力值低於標準\n規範壓力值: 6 kg/cm^2\n目前壓力值: " + \
                              str(ds_temp['infusion_pressure'])[:3] + " kg/cm^2\n目前真空值: " + str(ds_temp['infusion_vacuum'])[:3] + " torr"

                    status = message
                    time_out = time_in + 1
                    flag = 4

            # 二次洩壓中
            elif flag == 5 and ds_temp['pre_status'] == 2 and ds_temp_next['pre_status'] == 2:
                status = "洩壓中"
                time_out = 2
                flag = 5

            # 完全洩壓/製程結束
            elif flag == 5 and ds_temp['pre_status'] == 2 and ds_temp_next['pre_status'] == 1:
                status = "製程結束"
                time_out = 2
                flag = 6

            # 重設flag
            elif flag == 6:
                time_out = 2
                flag = 0

            else:
                message = vpi_ad + "製程異常"
                status = message
                time_out = time_in + 1
                flag = 0

    print("time_out:", time_out)
    print(status, ds_temp["time"])
    # ln.line_notify(message, time_in)
    return flag, time_out
    # cycle.to_csv("cycle_test.csv")

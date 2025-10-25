import numpy as np
import matplotlib.pyplot as plt
from matplotlib.widgets import Slider, Button

# 设置中文显示
plt.rcParams['font.sans-serif'] = ['Microsoft YaHei']
plt.rcParams["axes.unicode_minus"] = False  # 解决负号显示问题
plt.rcParams["font.size"] = 9  # 标注字体大小


def calculate_intensity(d, L, wavelength, bandwidth):
    """计算双缝干涉光强分布及明纹位置"""
    x = np.linspace(-0.1, 0.1, 1000)  # 屏幕x坐标（米）
    theta = np.arctan(x / L)  # 光线与法线夹角

    if bandwidth == 0:
        # 理想单色光
        intensity = 4 * np.cos(np.pi * d * np.sin(theta) / wavelength) ** 2
    else:
        # 非单色光（叠加带宽内的波长）
        wavelengths = np.linspace(wavelength - bandwidth / 2, wavelength + bandwidth / 2, 5)
        total_intensity = np.zeros_like(x)
        for lam in wavelengths:
            total_intensity += 4 * np.cos(np.pi * d * np.sin(theta) / lam) ** 2
        intensity = total_intensity / len(wavelengths)

    # 计算条纹间距△x（理论值：△x = λL/d）
    delta_x = (wavelength * L) / d if d != 0 else 0

    # 计算明纹位置（k=0,±1,±2,...）及序号
    k_max = int(0.08 / delta_x) if delta_x != 0 else 3  # 限制标注数量
    k_values = np.arange(-k_max, k_max + 1)
    bright_positions = (k_values * wavelength * L) / d  # 明纹位置公式：x = kλL/d
    # 过滤超出显示范围的明纹
    valid_mask = (bright_positions >= x.min()) & (bright_positions <= x.max())
    bright_positions = bright_positions[valid_mask]
    k_values = k_values[valid_mask]

    return x, intensity, delta_x, bright_positions, k_values


# 创建主画布
fig = plt.figure(figsize=(14, 8))

# 左侧图像区域
ax_stripes = fig.add_axes([0.05, 0.55, 0.6, 0.4])  # 上：干涉条纹
ax_intensity = fig.add_axes([0.05, 0.1, 0.6, 0.4])  # 下：光强曲线

# 右侧控制区域
ax_control = fig.add_axes([0.68, 0.1, 0.3, 0.85])
ax_control.axis('off')

# 右侧子区域
ax_params = ax_control.inset_axes([0, 0.6, 1, 0.4])  # 参数显示区
ax_params.axis('off')
ax_sliders = ax_control.inset_axes([0, 0.15, 1, 0.45])  # 滑块区
ax_sliders.axis('off')
ax_button = ax_control.inset_axes([0.2, 0, 0.6, 0.1])  # 按钮区

# 初始参数
d_init = 0.5e-3  # 0.5mm
L_init = 2.0  # 2米
lambda_init = 632e-9  # 632nm
bandwidth_init = 0e-9  # 0nm

# 存储标注和参考线对象
stripe_labels = []
intensity_labels = []
global k0_line_stripes, k0_line_intensity  # k=0红线对象


# 初始化图像
def init_plot():
    global k0_line_stripes, k0_line_intensity, stripe_labels, intensity_labels
    # 计算初始数据
    x, intensity, delta_x, bright_pos, k_vals = calculate_intensity(
        d_init, L_init, lambda_init, bandwidth_init
    )

    # 干涉条纹（竖直条纹）
    y = np.linspace(0, 0.1, 100)
    intensity_2d = np.tile(intensity[np.newaxis, :], (len(y), 1))
    global stripe_img
    stripe_img = ax_stripes.imshow(
        intensity_2d, cmap='gray', aspect='auto',
        extent=[x.min(), x.max(), y.min(), y.max()], origin='lower'
    )
    ax_stripes.set_title('杨氏双缝干涉条纹（竖直方向）')
    ax_stripes.set_ylabel('屏幕y坐标 (m)')
    ax_stripes.set_xlabel('屏幕x坐标 (m)')

    # 添加k=0红色参考线（干涉条纹图）
    k0_line_stripes = ax_stripes.axvline(x=0, color='red', linestyle='--', linewidth=2, alpha=0.8)

    # 光强分布曲线
    global intensity_line
    intensity_line, = ax_intensity.plot(x, intensity, 'b-', linewidth=2)
    ax_intensity.set_title('光强分布曲线')
    ax_intensity.set_xlabel('屏幕x坐标 (m)')
    ax_intensity.set_ylabel('相对光强')
    ax_intensity.grid(True)
    ax_intensity.set_ylim(-0.1, 4.1)

    # 添加k=0红色参考线（光强曲线图）
    k0_line_intensity = ax_intensity.axvline(x=0, color='red', linestyle='--', linewidth=2, alpha=0.8)

    # 初始标注明纹序号
    update_labels(bright_pos, k_vals)


def update_labels(bright_positions, k_values):
    """更新条纹序号标注"""
    global stripe_labels, intensity_labels
    # 清除旧标注
    for label in stripe_labels:
        label.remove()
    for label in intensity_labels:
        label.remove()
    stripe_labels = []
    intensity_labels = []

    # 添加新标注
    for x_pos, k in zip(bright_positions, k_values):
        label_text = f'k{k}' if k != 0 else 'k0 (中央明纹)'  # k0标注更明确
        # 干涉条纹图上的标注
        stripe_label = ax_stripes.text(
            x_pos, 0.08, label_text,
            ha='center', va='center',
            bbox=dict(facecolor='white', alpha=0.7, boxstyle='round,pad=0.3')
        )
        stripe_labels.append(stripe_label)

        # 光强曲线图上的标注
        intensity_label = ax_intensity.text(
            x_pos, 3.8, label_text,
            ha='center', va='center',
            bbox=dict(facecolor='white', alpha=0.7, boxstyle='round,pad=0.3')
        )
        intensity_labels.append(intensity_label)


# 更新图像函数
def update(val):
    # 获取参数并转换单位
    d = d_slider.val * 1e-3
    L = L_slider.val
    wavelength = lambda_slider.val * 1e-9
    bandwidth = bandwidth_slider.val * 1e-9

    # 计算光强、条纹间距和明纹位置
    x, intensity, delta_x, bright_pos, k_vals = calculate_intensity(
        d, L, wavelength, bandwidth
    )

    # 更新干涉条纹
    y = np.linspace(0, 0.1, 100)
    intensity_2d = np.tile(intensity[np.newaxis, :], (len(y), 1))
    stripe_img.set_data(intensity_2d)
    stripe_img.set_extent([x.min(), x.max(), y.min(), y.max()])

    # 更新光强曲线
    intensity_line.set_xdata(x)
    intensity_line.set_ydata(intensity)
    ax_intensity.set_xlim(x.min(), x.max())

    # 更新条纹序号标注
    update_labels(bright_pos, k_vals)

    # 计算单色性参数
    monochromaticity = (bandwidth / wavelength) if wavelength != 0 else 0

    # 更新右侧参数文本
    ax_params.clear()
    ax_params.axis('off')
    param_text = f"""
    实验参数：

    双缝间距: {d_slider.val:.1f} mm
    缝屏距离: {L_slider.val:.1f} m
    入射光波长: {lambda_slider.val:.0f} nm
    带宽: {bandwidth_slider.val:.0f} nm

    带宽说明：
    带宽表示光源波长的分布范围，0表示理想单色光（单一波长），
    数值越大说明光源包含的波长范围越广，单色性越差，
    干涉条纹的可见度会随带宽增大而降低（条纹逐渐模糊）。

    计算结果：
    条纹间距△x: {delta_x * 1e3:.3f} mm
    光源单色性: {monochromaticity:.6f}
    （单色性=带宽/波长，值越小表示光源纯度越高）
    """
    ax_params.text(0, 0.95, param_text, fontsize=10, verticalalignment='top', wrap=True)

    # 刷新图像
    fig.canvas.draw_idle()


# 重置按钮功能
def reset(event):
    d_slider.reset()
    L_slider.reset()
    lambda_slider.reset()
    bandwidth_slider.reset()


# 初始化图像
init_plot()

# 创建右侧滑块
slider_height = 0.15
slider_margin = 0.08
ax_d = ax_sliders.inset_axes([0.1, 1 - slider_height - slider_margin * 0, 0.8, 0.1])
d_slider = Slider(ax_d, '双缝间距 (mm)', 0.1, 2.0, valinit=d_init * 1e3)

ax_L = ax_sliders.inset_axes([0.1, 1 - slider_height * 2 - slider_margin * 1, 0.8, 0.1])
L_slider = Slider(ax_L, '缝屏距离 (m)', 0.5, 5.0, valinit=L_init)

ax_lambda = ax_sliders.inset_axes([0.1, 1 - slider_height * 3 - slider_margin * 2, 0.8, 0.1])
lambda_slider = Slider(ax_lambda, '波长 (nm)', 400, 700, valinit=lambda_init * 1e9)

ax_bandwidth = ax_sliders.inset_axes([0.1, 1 - slider_height * 4 - slider_margin * 3, 0.8, 0.1])
bandwidth_slider = Slider(ax_bandwidth, '带宽 (nm)', 0, 50, valinit=bandwidth_init * 1e9)

# 绑定更新事件
d_slider.on_changed(update)
L_slider.on_changed(update)
lambda_slider.on_changed(update)
bandwidth_slider.on_changed(update)

# 重置按钮
reset_button = Button(ax_button, '重置参数')
reset_button.on_clicked(reset)

# 初始化参数显示
update(None)

# 显示图像
plt.show()
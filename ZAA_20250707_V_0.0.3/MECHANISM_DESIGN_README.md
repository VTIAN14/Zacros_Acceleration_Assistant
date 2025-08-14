# Mechanism Design 功能说明

## 功能概述
新的 Mechanism Design 功能位于主菜单的 "Pattern Design and Feasible Check" -> "Mechanism Design"，用于设计反应机理。

## 界面布局
```
┌─────────────────┬─────────────────┐
│  Initial State  │   Final State   │
│   Lattice Plot  │   Lattice Plot  │
├─────────────────┼─────────────────┤
│  Initial State  │   Final State   │
│  Site Selector  │  Site Selector  │
├─────────────────┴─────────────────┤
│        Mechanism Generation       │
│         (Name + Output)           │
└───────────────────────────────────┘
```

## 使用步骤

### 1. 选择文件夹
首先在主界面选择包含 lattice_input.dat 和 energetics_input.dat 的文件夹。

### 2. 打开 Mechanism Design
点击菜单 "Pattern Design and Feasible Check" -> "Mechanism Design"

### 3. 设置初始状态
- 在左边的 Site Selector 中选择物种
- 点击左上角的 lattice plot 中的位点来放置物种
- 选择的位点会用不同颜色高亮显示
- 位点列表会显示所有选择的位点和对应的物种

### 4. 设置最终状态
- 在右边的 Site Selector 中选择物种
- 点击右上角的 lattice plot 中的位点来放置物种
- 可以选择与初始状态不同的位点和物种

### 5. 生成机理
- 输入反应名称（默认为 "reaction_1"）
- 点击 "Generate Mechanism" 按钮
- 生成的机理文本会显示在底部的文本框中
- 文本会自动复制到剪贴板

## 功能特点

### 双lattice显示
- 左右两个相同的晶格图
- 可以独立选择不同的位点配置
- 实时更新位点显示

### Site Selector
- 下拉菜单选择可用的物种
- 点击按钮提示用户在晶格上点击
- 站点列表显示当前选择
- 清除按钮重置选择

### 自动生成机理文本
- 基于选择的初始和最终状态
- 生成标准的 Zacros 反应步骤格式
- 包含位点映射和邻居信息
- 自动复制到剪贴板

## 生成的文本格式示例
```
# reaction_1

# Initial State
site 1: CH3*_Cu
site 2: O*_Cu

# Final State
site 1: CH2*_Cu
site 3: OH*_Cu

# Reaction Step
reversible_step reaction_1
  gas_reacs_prods
    # Add gas phase species here
  sites
    3
  initial
    1 CH3*_Cu 1
    2 O*_Cu 2
    3 * 3
  final
    1 CH2*_Cu 1
    2 * 2
    3 OH*_Cu 3
  neighboring
    1-2
    2-3
  absl_activation_eng    0.5  # Adjust as needed
end_reversible_step
```

## 控制按钮说明
- **Click on lattice to add site**: 提示用户在lattice上点击选择位点
- **Clear All Sites**: 清除该侧所有选择的位点
- **Generate Mechanism**: 基于两侧的位点选择生成机理文本

## 注意事项
1. 需要先在主界面选择包含 lattice 和 energetics 文件的文件夹
2. 初始状态和最终状态可以选择不同的位点组合
3. 生成的机理文本是基础模板，可能需要手动调整激活能等参数
4. 文本会自动复制到剪贴板，可以直接粘贴使用

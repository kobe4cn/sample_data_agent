# Visualization - Chinese Font Support

## ADDED Requirements

### Requirement: Chinese Character Rendering Support

The visualization system SHALL support rendering Chinese characters (Simplified and Traditional) in matplotlib plots, including axis labels, titles, legends, and annotations.

#### Scenario: Chinese axis labels displayed correctly
- **WHEN** user generates a plot with Chinese column names as axis labels (e.g., `plt.xlabel('月收入')`)
- **THEN** the Chinese characters SHALL be rendered correctly without displaying as boxes or garbled text

#### Scenario: Chinese title and legend support
- **WHEN** user creates a plot with Chinese text in title or legend (e.g., `plt.title('客户流失分析')`, `plt.legend(['已流失', '未流失'])`)
- **THEN** all Chinese characters SHALL be displayed properly in the generated image

#### Scenario: Mixed Chinese and English text
- **WHEN** user uses both Chinese and English in plot labels (e.g., `xlabel('Customer 类型')`)
- **THEN** both Chinese and English characters SHALL be rendered correctly

### Requirement: Cross-Platform Font Detection

The system SHALL automatically detect and configure appropriate Chinese fonts based on the operating system.

#### Scenario: Font selection on macOS
- **WHEN** the sandbox initializes on macOS
- **THEN** the system SHALL attempt to use fonts in order: PingFang SC, Heiti TC, STHeiti, Arial Unicode MS

#### Scenario: Font selection on Windows
- **WHEN** the sandbox initializes on Windows
- **THEN** the system SHALL attempt to use fonts in order: Microsoft YaHei, SimHei, SimSun, FangSong

#### Scenario: Font selection on Linux
- **WHEN** the sandbox initializes on Linux
- **THEN** the system SHALL attempt to use fonts in order: WenQuanYi Micro Hei, Droid Sans Fallback, Noto Sans CJK SC

#### Scenario: No Chinese font available
- **WHEN** no Chinese font is found on the system
- **THEN** the system SHALL log a warning message and continue using the default font without failing

### Requirement: Graceful Degradation

The font configuration system SHALL not break existing functionality when Chinese fonts are unavailable.

#### Scenario: Fallback to default behavior
- **WHEN** Chinese font configuration fails for any reason
- **THEN** the visualization tool SHALL continue to work with default matplotlib fonts
- **AND** a warning SHALL be logged indicating the font configuration issue

#### Scenario: Existing English plots unaffected
- **WHEN** user generates plots with only English text
- **THEN** the plots SHALL render identically to before Chinese font support was added

### Requirement: Python Visualization Code Execution

The system SHALL execute Python plotting code and save generated figures to image files, supporting both English and Chinese text content.

#### Scenario: Plot generation with Chinese labels
- **WHEN** user submits valid matplotlib code with Chinese text elements
- **THEN** the code SHALL execute successfully and generate a valid PNG image with correctly rendered Chinese characters

#### Scenario: Error handling for plotting code
- **WHEN** the plotting code contains syntax errors or runtime errors
- **THEN** a descriptive error message SHALL be returned to the user
- **AND** the error message SHALL not be caused by Chinese character encoding issues

#### Scenario: Figure object validation
- **WHEN** the plotting code creates a matplotlib Figure object
- **THEN** the system SHALL extract and save the figure regardless of whether it contains Chinese or English text

"""
Validation tests for JavaScript files.
Tests syntax, structure, and best practices for uploader.js and video_player.js
"""
import pytest
import re
import os


class TestUploaderJSValidation:
    """Validation tests for uploader.js file."""
    
    @pytest.fixture
    def uploader_js_content(self):
        """Read the uploader.js file content."""
        with open('static/js/uploader.js', 'r') as f:
            return f.read()
    
    def test_uploader_js_file_exists(self):
        """Test that uploader.js file exists."""
        assert os.path.exists('static/js/uploader.js')
    
    def test_uploader_defines_required_elements(self, uploader_js_content):
        """Test that uploader.js defines all required DOM elements."""
        required_elements = [
            'uploadBoxImage',
            'fileInputImage',
            'placeholderImage',
            'uploadBoxVideo',
            'fileInputVideo',
            'placeholderVideo'
        ]
        
        for element in required_elements:
            assert element in uploader_js_content, f"Missing element: {element}"
    
    def test_uploader_defines_showtoast_function(self, uploader_js_content):
        """Test that uploader.js defines showToast function."""
        assert 'function showToast(' in uploader_js_content
        assert 'toast-container' in uploader_js_content
    
    def test_uploader_handles_image_click(self, uploader_js_content):
        """Test that uploader.js handles image upload box click events."""
        assert "uploadBoxImage.addEventListener('click'" in uploader_js_content
        assert 'fileInputImage.click()' in uploader_js_content
    
    def test_uploader_handles_video_click(self, uploader_js_content):
        """Test that uploader.js handles video upload box click events."""
        assert "uploadBoxVideo.addEventListener('click'" in uploader_js_content
        assert 'fileInputVideo.click()' in uploader_js_content
    
    def test_uploader_handles_dragover_events(self, uploader_js_content):
        """Test that uploader.js handles dragover events."""
        assert "addEventListener('dragover'" in uploader_js_content
        assert 'e.preventDefault()' in uploader_js_content
        assert "classList.add('dragover')" in uploader_js_content
    
    def test_uploader_handles_dragleave_events(self, uploader_js_content):
        """Test that uploader.js handles dragleave events."""
        assert "addEventListener('dragleave'" in uploader_js_content
        assert "classList.remove('dragover')" in uploader_js_content
    
    def test_uploader_handles_drop_events(self, uploader_js_content):
        """Test that uploader.js handles drop events."""
        assert "addEventListener('drop'" in uploader_js_content
        assert 'dataTransfer.files' in uploader_js_content
    
    def test_uploader_validates_image_mime_type(self, uploader_js_content):
        """Test that uploader.js validates image MIME types."""
        assert "file.type.startsWith('image/')" in uploader_js_content
    
    def test_uploader_validates_video_mime_type(self, uploader_js_content):
        """Test that uploader.js validates video MIME types."""
        assert "file.type.startsWith('video/')" in uploader_js_content
    
    def test_uploader_shows_warning_for_invalid_files(self, uploader_js_content):
        """Test that uploader.js shows warnings for invalid file types."""
        assert "showToast(" in uploader_js_content
        assert "'warning'" in uploader_js_content
    
    def test_uploader_updates_placeholder_text(self, uploader_js_content):
        """Test that uploader.js updates placeholder text when files are selected."""
        assert 'placeholderImage.textContent' in uploader_js_content
        assert 'placeholderVideo.textContent' in uploader_js_content
        assert 'Selected:' in uploader_js_content
    
    def test_uploader_no_syntax_errors(self, uploader_js_content):
        """Test that uploader.js has no obvious syntax errors."""
        # Check for balanced braces
        open_braces = uploader_js_content.count('{')
        close_braces = uploader_js_content.count('}')
        assert open_braces == close_braces, "Unbalanced braces in uploader.js"
        
        # Check for balanced parentheses
        open_parens = uploader_js_content.count('(')
        close_parens = uploader_js_content.count(')')
        assert open_parens == close_parens, "Unbalanced parentheses in uploader.js"


class TestVideoPlayerJSValidation:
    """Validation tests for video_player.js file."""
    
    @pytest.fixture
    def video_player_js_content(self):
        """Read the video_player.js file content."""
        with open('static/js/video_player.js', 'r') as f:
            return f.read()
    
    def test_video_player_js_file_exists(self):
        """Test that video_player.js file exists."""
        assert os.path.exists('static/js/video_player.js')
    
    def test_video_player_waits_for_dom_ready(self, video_player_js_content):
        """Test that video_player.js waits for DOM to be ready."""
        assert 'DOMContentLoaded' in video_player_js_content
    
    def test_video_player_selects_video_containers(self, video_player_js_content):
        """Test that video_player.js selects video containers."""
        assert 'querySelectorAll' in video_player_js_content
        assert 'video-container' in video_player_js_content
    
    def test_video_player_defines_helper_functions(self, video_player_js_content):
        """Test that video_player.js defines required helper functions."""
        helper_functions = [
            'formatTime',
            'updateSliderBackground',
            'togglePlayPause',
            'updatePlayPauseButton',
            'updateProgressBar',
            'seekVideo',
            'toggleMute',
            'updateMuteButton',
            'changeVolume',
            'toggleFullscreen',
            'updateFullscreenButton'
        ]
        
        for func in helper_functions:
            assert f'function {func}(' in video_player_js_content, f"Missing function: {func}"
    
    def test_video_player_handles_hls_support(self, video_player_js_content):
        """Test that video_player.js handles HLS.js support detection."""
        assert 'Hls.isSupported()' in video_player_js_content
        assert 'hlsInstance = new Hls()' in video_player_js_content
    
    def test_video_player_handles_native_hls(self, video_player_js_content):
        """Test that video_player.js handles native HLS support (Safari)."""
        assert "canPlayType('application/vnd.apple.mpegurl')" in video_player_js_content
    
    def test_video_player_handles_quality_selection(self, video_player_js_content):
        """Test that video_player.js handles quality level selection."""
        assert 'buildQualityOptions' in video_player_js_content
        assert 'selectQualityLevel' in video_player_js_content
        assert 'currentQualityLevel' in video_player_js_content
    
    def test_video_player_handles_playback_speed(self, video_player_js_content):
        """Test that video_player.js handles playback speed changes."""
        assert 'changePlaybackSpeed' in video_player_js_content
        assert 'playbackRate' in video_player_js_content
    
    def test_video_player_handles_picture_in_picture(self, video_player_js_content):
        """Test that video_player.js handles Picture-in-Picture."""
        assert 'togglePip' in video_player_js_content
        assert 'requestPictureInPicture' in video_player_js_content
        assert 'exitPictureInPicture' in video_player_js_content
    
    def test_video_player_handles_fullscreen(self, video_player_js_content):
        """Test that video_player.js handles fullscreen functionality."""
        assert 'requestFullscreen' in video_player_js_content
        assert 'exitFullscreen' in video_player_js_content
        assert 'fullscreenElement' in video_player_js_content
    
    def test_video_player_handles_controls_visibility(self, video_player_js_content):
        """Test that video_player.js handles controls auto-hide."""
        assert 'hideControls' in video_player_js_content
        assert 'showControls' in video_player_js_content
        assert 'hideControlsAfterDelay' in video_player_js_content
    
    def test_video_player_attaches_event_listeners(self, video_player_js_content):
        """Test that video_player.js attaches necessary event listeners."""
        events = [
            'play',
            'pause',
            'ended',
            'timeupdate',
            'loadedmetadata',
            'volumechange',
            'fullscreenchange',
            'click',
            'mouseenter',
            'mousemove',
            'mouseleave'
        ]
        
        for event in events:
            assert f"'{event}'" in video_player_js_content or f'"{event}"' in video_player_js_content
    
    def test_video_player_handles_hls_events(self, video_player_js_content):
        """Test that video_player.js handles HLS.js events."""
        assert 'Hls.Events.MANIFEST_PARSED' in video_player_js_content
        assert 'Hls.Events.LEVEL_SWITCHED' in video_player_js_content
    
    def test_video_player_formats_time_correctly(self, video_player_js_content):
        """Test that video_player.js formats time with proper padding."""
        assert 'padStart(2, "0")' in video_player_js_content or "padStart(2, '0')" in video_player_js_content
    
    def test_video_player_no_syntax_errors(self, video_player_js_content):
        """Test that video_player.js has no obvious syntax errors."""
        # Check for balanced braces
        open_braces = video_player_js_content.count('{')
        close_braces = video_player_js_content.count('}')
        assert open_braces == close_braces, "Unbalanced braces in video_player.js"
        
        # Check for balanced parentheses
        open_parens = video_player_js_content.count('(')
        close_parens = video_player_js_content.count(')')
        assert open_parens == close_parens, "Unbalanced parentheses in video_player.js"
    
    def test_video_player_uses_const_and_let(self, video_player_js_content):
        """Test that video_player.js uses modern JavaScript (const/let)."""
        # Should use const or let, not var
        assert 'const ' in video_player_js_content or 'let ' in video_player_js_content
    
    def test_video_player_handles_status_attribute(self, video_player_js_content):
        """Test that video_player.js reads video status from data attribute."""
        assert 'dataset.status' in video_player_js_content
        assert 'dataset.url' in video_player_js_content


class TestCSSValidation:
    """Validation tests for CSS files."""
    
    def test_video_controls_css_exists(self):
        """Test that video_controls.css file exists."""
        assert os.path.exists('static/css/video_controls.css')
    
    def test_video_controls_css_defines_container(self):
        """Test that video_controls.css defines video-container styles."""
        with open('static/css/video_controls.css', 'r') as f:
            content = f.read()
        
        assert '.video-container' in content
    
    def test_video_controls_css_defines_controls_overlay(self):
        """Test that video_controls.css defines controls overlay styles."""
        with open('static/css/video_controls.css', 'r') as f:
            content = f.read()
        
        assert '.controls-overlay' in content
        assert '.controls-bar' in content
    
    def test_video_controls_css_defines_play_overlay(self):
        """Test that video_controls.css defines play overlay styles."""
        with open('static/css/video_controls.css', 'r') as f:
            content = f.read()
        
        assert '.play-overlay' in content
    
    def test_video_controls_css_uses_css_variables(self):
        """Test that video_controls.css uses CSS custom properties."""
        with open('static/css/video_controls.css', 'r') as f:
            content = f.read()
        
        # Should reference CSS variables like --primary-color
        assert 'var(--' in content
    
    def test_style_css_includes_video_styles(self):
        """Test that style.css includes video-related styles."""
        with open('static/css/style.css', 'r') as f:
            content = f.read()
        
        # Check for video-related additions
        assert '.video-js' in content or '.player' in content


class TestSVGIconsValidation:
    """Validation tests for SVG icon files."""
    
    def test_required_svg_icons_exist(self):
        """Test that all required SVG icons exist."""
        required_icons = [
            'play.svg',
            'pause.svg',
            'fullscreen.svg',
            'fullscreen-exit.svg',
            'volume-up.svg',
            'volume-mute.svg',
            'gear.svg',
            'pip.svg'
        ]
        
        for icon in required_icons:
            icon_path = f'static/svg/{icon}'
            assert os.path.exists(icon_path), f"Missing icon: {icon}"
    
    def test_svg_icons_are_valid_xml(self):
        """Test that SVG files contain valid SVG structure."""
        svg_dir = 'static/svg'
        if os.path.exists(svg_dir):
            for filename in os.listdir(svg_dir):
                if filename.endswith('.svg'):
                    filepath = os.path.join(svg_dir, filename)
                    with open(filepath, 'r') as f:
                        content = f.read()
                    
                    # Basic SVG validation
                    assert '<svg' in content, f"{filename} missing <svg> tag"
                    # Most icons should have viewBox
                    # (not strictly required but good practice)


class TestTemplateVideoComponentValidation:
    """Validation tests for video_player.html template component."""
    
    def test_video_player_template_exists(self):
        """Test that video_player.html template component exists."""
        assert os.path.exists('templates/components/video_player.html')
    
    def test_video_player_template_structure(self):
        """Test that video_player.html has correct structure."""
        with open('templates/components/video_player.html', 'r') as f:
            content = f.read()
        
        # Should have video container
        assert 'video-container' in content
        
        # Should have video element
        assert '<video' in content
        
        # Should have controls
        assert 'controls-overlay' in content
        assert 'progress-bar' in content
    
    def test_video_player_template_uses_data_attributes(self):
        """Test that video_player template uses data attributes for configuration."""
        with open('templates/components/video_player.html', 'r') as f:
            content = f.read()
        
        # Should use data attributes for URL and status
        assert 'data-url' in content
        assert 'data-status' in content


class TestIntegrationPoints:
    """Test integration points between files."""
    
    def test_layout_includes_video_scripts(self):
        """Test that layout.html includes video player scripts."""
        with open('templates/layout.html', 'r') as f:
            content = f.read()
        
        # Should include HLS.js
        assert 'hls.min.js' in content or 'hls.js' in content
        
        # Should include video_player.js
        assert 'video_player.js' in content
    
    def test_new_post_template_includes_uploader(self):
        """Test that new.html includes uploader.js."""
        with open('templates/new.html', 'r') as f:
            content = f.read()
        
        assert 'uploader.js' in content
    
    def test_edit_template_includes_uploader(self):
        """Test that edit.html includes uploader.js."""
        with open('templates/edit.html', 'r') as f:
            content = f.read()
        
        assert 'uploader.js' in content
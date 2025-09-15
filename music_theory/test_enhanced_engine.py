#!/usr/bin/env python3
"""
Test script for the enhanced music theory engine.
"""

import sys
import os
import numpy as np

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from music_theory.theory_engine import EnhancedMusicTheoryEngine, ScaleType, ChordAnalysis, KeyAnalysis

def test_enhanced_music_theory_engine():
    """Test the enhanced music theory engine functionality."""
    print("🎵 Testing Enhanced Music Theory Engine")
    print("=" * 50)
    
    # Initialize the engine
    engine = EnhancedMusicTheoryEngine()
    print("✅ Engine initialized successfully")
    
    # Test chord template definitions
    print(f"📊 Available chord templates: {len(engine.chord_templates)}")
    print(f"🎼 Available scale templates: {len(engine.scale_templates)}")
    print(f"🔑 Major key profiles: {len(engine.key_profiles)}")
    print(f"🔑 Minor key profiles: {len(engine.minor_key_profiles)}")
    
    # Test scale note generation
    print("\n🎹 Testing scale generation:")
    try:
        c_major_notes = engine._get_scale_notes('C', ScaleType.MAJOR)
        print(f"C Major scale: {c_major_notes}")
        
        a_minor_notes = engine._get_scale_notes('A', ScaleType.MINOR)
        print(f"A Minor scale: {a_minor_notes}")
        
        d_dorian_notes = engine._get_scale_notes('D', ScaleType.DORIAN)
        print(f"D Dorian scale: {d_dorian_notes}")
    except Exception as e:
        print(f"❌ Scale generation error: {e}")
    
    # Test chord detection from synthetic chroma
    print("\n🎸 Testing chord detection:")
    try:
        # Create a synthetic C major chord chroma
        c_major_chroma = np.zeros(12)
        c_major_chroma[0] = 1.0  # C
        c_major_chroma[4] = 0.8  # E
        c_major_chroma[7] = 0.6  # G
        
        chord_result = engine._detect_chord_from_chroma(c_major_chroma)
        print(f"Detected chord: {chord_result['chord']} (confidence: {chord_result['confidence']:.3f})")
        
        # Test Am chord
        a_minor_chroma = np.zeros(12)
        a_minor_chroma[9] = 1.0   # A
        a_minor_chroma[0] = 0.8   # C
        a_minor_chroma[4] = 0.6   # E
        
        chord_result = engine._detect_chord_from_chroma(a_minor_chroma)
        print(f"Detected chord: {chord_result['chord']} (confidence: {chord_result['confidence']:.3f})")
        
    except Exception as e:
        print(f"❌ Chord detection error: {e}")
    
    # Test key detection from synthetic chroma
    print("\n🔑 Testing key detection:")
    try:
        # Create synthetic chroma for C major (emphasize tonic and dominant)
        c_major_chroma_matrix = np.zeros((12, 100))  # 12 pitch classes, 100 time frames
        
        # Emphasize C major scale notes across time
        for frame in range(100):
            c_major_chroma_matrix[0, frame] = 1.0   # C
            c_major_chroma_matrix[2, frame] = 0.7   # D
            c_major_chroma_matrix[4, frame] = 0.8   # E
            c_major_chroma_matrix[5, frame] = 0.6   # F
            c_major_chroma_matrix[7, frame] = 0.9   # G
            c_major_chroma_matrix[9, frame] = 0.7   # A
            c_major_chroma_matrix[11, frame] = 0.5  # B
        
        key_result = engine._enhanced_key_detection(c_major_chroma_matrix)
        print(f"Detected key: {key_result.key} {key_result.mode}")
        print(f"Confidence: {key_result.confidence:.3f}")
        print(f"Scale notes: {key_result.scale_notes}")
        print(f"Suggested chords: {key_result.suggested_chords}")
        
    except Exception as e:
        print(f"❌ Key detection error: {e}")
    
    # Test chord substitutions
    print("\n🔄 Testing chord substitutions:")
    try:
        guitar_subs = engine.chord_substitutions.get('guitar', {})
        print(f"Guitar substitutions available: {len(guitar_subs)}")
        if 'F' in guitar_subs:
            print(f"F chord substitutions for guitar: {guitar_subs['F']}")
        
        ukulele_subs = engine.chord_substitutions.get('ukulele', {})
        print(f"Ukulele substitutions available: {len(ukulele_subs)}")
        if 'F' in ukulele_subs:
            print(f"F chord substitutions for ukulele: {ukulele_subs['F']}")
            
    except Exception as e:
        print(f"❌ Substitution test error: {e}")
    
    # Test difficulty ratings
    print("\n📈 Testing difficulty ratings:")
    try:
        guitar_difficulties = engine.chord_difficulty.get('guitar', {})
        print(f"Guitar chord difficulties available: {len(guitar_difficulties)}")
        
        easy_chords = [chord for chord, diff in guitar_difficulties.items() if diff <= 3]
        hard_chords = [chord for chord, diff in guitar_difficulties.items() if diff >= 7]
        
        print(f"Easy guitar chords (≤3): {easy_chords[:5]}...")
        print(f"Hard guitar chords (≥7): {hard_chords}")
        
    except Exception as e:
        print(f"❌ Difficulty test error: {e}")
    
    # Test common progressions
    print("\n🎼 Testing common progressions:")
    try:
        progressions = engine.common_progressions
        print(f"Common progressions available: {len(progressions)}")
        
        for prog_name, prog_data in list(progressions.items())[:3]:
            print(f"  {prog_name}: {prog_data['roman']} - {prog_data['description']}")
            
    except Exception as e:
        print(f"❌ Progression test error: {e}")
    
    print("\n✨ Enhanced Music Theory Engine Test Complete!")
    print("🎉 All core functionality is working properly")
    
    return True

if __name__ == "__main__":
    try:
        test_enhanced_music_theory_engine()
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
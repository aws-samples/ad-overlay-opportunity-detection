# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.

# Permission is hereby granted, free of charge, to any person obtaining a copy of
# this software and associated documentation files (the "Software"), to deal in
# the Software without restriction, including without limitation the rights to
# use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of
# the Software, and to permit persons to whom the Software is furnished to do so.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS
# FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR
# COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER
# IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN
# CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

MILLISECS_PER_HOUR = 1000 * 60 * 60
MILLISECS_PER_MINUTE = 1000 * 60


class AdOpportunites:
    def __init__(self, min_ad_duration_in_seconds):
        self.min_ad_duration_in_msec = min_ad_duration_in_seconds * 1000
        self.text_shown_segments = []

    def set_video_length(self, total_video_length_in_ms):
        self.video_length_in_ms = total_video_length_in_ms

    def add_text_presence(self, timestamp):
        """
        add a new segment if:
            1. there aren't any yet
            -or-
            2. the new timestamp is beyond the minimum_ad_duration of the latest one
        otherwise just extend the latest segment
        """
        if len(self.text_shown_segments) == 0:
            print(f'Starting new segment at {timestamp}')
            self.text_shown_segments.append({'start': timestamp, 'end': timestamp})
        else:
            latest_segment = self.text_shown_segments[-1]
            time_since_last_segment = timestamp - latest_segment['end']
            if time_since_last_segment < self.min_ad_duration_in_msec:
                print(f'Extending last segment to be {timestamp}')
                latest_segment['end'] = timestamp
            else:
                print(f'Adding new segment at {timestamp}')
                self.text_shown_segments.append({'start': timestamp, 'end': timestamp})

    def format_time(self, number_of_ms):
        num_hours = int(number_of_ms / MILLISECS_PER_HOUR)
        number_of_ms -= num_hours * MILLISECS_PER_HOUR
        num_minutes = int(number_of_ms / MILLISECS_PER_MINUTE)
        number_of_ms -= num_minutes * MILLISECS_PER_MINUTE
        num_seconds = int(number_of_ms / 1000)
        return f'{num_hours:02}:{num_minutes:02}:{num_seconds:02}'

    def get_available_placement_text(self):
        available_slots = []

        # treat the end as if it was another piece of text
        self.add_text_presence(self.video_length_in_ms)

        # and make sure we handle the start of the video, if there is room for an ad
        if self.text_shown_segments[0]['start'] > self.min_ad_duration_in_msec:
            self.text_shown_segments.insert(0, {'start': 0, 'end': 0})

        # calculate the slots
        for segment_number in range(0, len(self.text_shown_segments) - 1):
            last_segment_end = self.text_shown_segments[segment_number]['end']
            next_segment_start = self.text_shown_segments[segment_number + 1]['start']
            # add 1 second padding to the end of one and the start of the next, since
            # Rekognition tends to detect text in videos at 1 second intervals
            last_segment_end += 1000
            next_segment_start -= 1000
            intra_segment_length_in_msec = next_segment_start - last_segment_end
            if intra_segment_length_in_msec > self.min_ad_duration_in_msec:
                start_segment_string = self.format_time(last_segment_end)
                end_segment_string = self.format_time(next_segment_start)
                segment_length_string = self.format_time(intra_segment_length_in_msec)
                new_slot_description = (
                    f"Available slot from {start_segment_string} to {end_segment_string}, "
                    f"duration: {segment_length_string}")
                available_slots.append(new_slot_description)

        # and then return a string with them
        return '\n'.join(available_slots)

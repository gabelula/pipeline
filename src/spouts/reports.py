from __future__ import absolute_import, print_function, unicode_literals

import traceback
from streamparse.spout import Spout

from helpers.report import ReportStreamEmitter


class S3ReportsSpout(Spout):

    def initialize(self, stormconf, context):
        self.report_emitter = ReportStreamEmitter('reports')
        self.reports = self.report_emitter.emit()

    def next_tuple(self):
        try:
            sanitised_report, raw_report = next(self.reports)
            report_id = sanitised_report['report_id']
            self.log("Next tuple is %s" % sanitised_report['record_type'])
            t = [report_id, sanitised_report['record_type'], sanitised_report]
            self.emit(t)
        except StopIteration:
            print("Finished")
        except Exception:
            error = traceback.format_exc()
            print("Failed to parse next report")
            print(error)

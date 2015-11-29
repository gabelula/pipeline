import os
import shutil
import logging

import luigi
import luigi.worker

from invoke.config import Config

from pipeline.helpers.util import get_luigi_target, list_report_files
# from pipeline.helpers.util import get_imported_dates
# from pipeline.helpers.report import header_avro

# from pipeline.batch.sanitise import AggregateYAMLReports

config = Config(runtime_path="invoke.yaml")
logger = logging.getLogger('ooni-pipeline')


class MoveReportFiles(luigi.Task):
    report_files = luigi.Parameter()
    dst_private = luigi.Parameter()

    def output(self):
        output = {}
        for report_file in self.report_files:
            dst = os.path.join(self.dst_private, os.path.basename(report_file))
            output[report_file] = get_luigi_target(
                dst, ssh_key_file=config.core.ssh_private_key_file,
                no_host_key_check=True)
        return output

    def run(self):
        output = self.output()
        for report_file in self.report_files:
            logger.info("Copying %s to %s" % (report_file,
                                              output[report_file].path))
            t = get_luigi_target(report_file,
                                 ssh_key_file=config.core.ssh_private_key_file,
                                 no_host_key_check=True)
            with t.open('r') as in_file:
                out_file = output[report_file].open('w')
                shutil.copyfileobj(in_file, out_file)
                out_file.close()
            t.remove()


def run(srcs, dst_private, worker_processes=16):
    sch = luigi.scheduler.CentralPlannerScheduler()
    w = luigi.worker.Worker(scheduler=sch,
                            worker_processes=worker_processes)

    for src in srcs:
        logging.info("Adding headers for src: %s" % src)
        report_files = list_report_files(
            src, key_file=config.core.ssh_private_key_file,
            no_host_key_check=True
        )
        task = MoveReportFiles(report_files=list(report_files),
                               dst_private=dst_private)
        w.add(task, multiprocess=True)
    w.run()
    w.stop()
    return report_files

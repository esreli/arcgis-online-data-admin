class ResultsReport(object):
    def __init__(self, results):
        if 'addResults' in results:
            self.add_success = filter(lambda result: result['success'], results['addResults'])
            self.add_failure = filter(lambda result: not result['success'], results['addResults'])
        if 'updateResults' in results:
            self.update_success = filter(lambda result: result['success'], results['updateResults'])
            self.update_failure = filter(lambda result: not result['success'], results['updateResults'])
        if 'deleteResults' in results:
            self.delete_success = filter(lambda result: result['success'], results['deleteResults'])
            self.delete_failure = filter(lambda result: not result['success'], results['deleteResults'])

    @property
    def adds(self):
        if self.add_success and self.add_failure:
            successes = [f'Success - OID: {add["objectId"]}' for add in self.add_success]
            failures = [f'Failure - OID: {add["objectId"]}, \'{add["error"]}\'' for add in self.add_failure]
            return successes + failures
        else:
            raise Exception("Results don't contain \'addResults\'")

    @property
    def updates(self):
        if self.update_success and self.update_failure:
            successes = [f'Success - OID: {update["objectId"]}' for update in self.update_success]
            failures = [f'Failure - OID: {update["objectId"]}, \'{update["error"]}\'' for update in self.update_failure]
            return successes + failures
        else:
            raise Exception("Results don't contain \'updateResults\'")

    @property
    def deletes(self):
        if self.delete_success and self.delete_failure:
            successes = [f'Success - OID: {delete["objectId"]}' for delete in self.delete_success]
            failures = [f'Failure - OID: {delete["objectId"]}, \'{delete["error"]}\'' for delete in self.delete_failure]
            return successes + failures
        else:
            raise Exception("Results don't contain \'deleteResults\'")

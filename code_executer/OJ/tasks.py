from celery.decorators import task
from .models import Submission
import subprocess
import os

@task(name="evaluate_submission")
def evaluate_submission(submission_id, test_case_id):
    try:
        submission = Submission.objects.get(id = submission_id)
    except:
        print("Submission with id = {} not found".format(submission_id))
        return
    test_case = TestCase.objects.get(id = test_case_id)
    container_id = subprocess.check_output(["docker", "run", "-it", "-m","256M","-d", "executer"])
    # decode bytestring to utf-8 and remove the last newline from docker output
    container_id = container_id.decode('utf-8')
    print(container_id)
    container_id = container_id[:len(container_id)-1]
    # this list can be appended to any command to make it run in container_id
    docker_lst  = ["docker", "exec", container_id]
    # first we'll copy our test case input and output files to the docker container
    # for this first we create a folder called testcases in the container
    # then move on to two docker cp commands
    print("creating file for test case")
    input_file_name = f"{test_case_id}.in"
    test_case_file_path = f"/tmp/{test_case_id}"
    user_test_case = open(test_case_file_path, "w+")
    print(test_case.input_text, file = user_test_case)
    user_test_case.close()
    print("file creation completed")
    subprocess.call(["docker", "cp", test_case_file_path, "{}:/{}".format(container_id, input_filename)])
    # the timeout_lst list makes sure that the user code does not run over the time limit
    # it makes use of the standard unix timeout command
    time_limit = 1
    timeout_lst = ["timeout", str(time_limit)]
    filename = '' # filename contains the name of the file which will contain the user's source code
    compiler = ''
    if submission.language == "C":
        filename = f'{submission_id}.c'
        compiler = 'gcc'
    elif submission.language == "CPP":
        filename = f'{submission_id}.cpp'
        compiler = 'g++'
    executable = f"{submission_id}.out"
    # converting the user's submitted code into a file that can be compiled here
    # file will be stored in submissions/
    print("creating a file for the submitted source code")
    user_code = open("/tmp/{}".format(filename), "w+")
    print(submission.code, file = user_code)
    user_code.close()
    print("file creation completed")
    print("copying file to docker container")
    subprocess.call(["docker", "cp", "/tmp/{}".format(filename), "{}:/{}".format(container_id, filename)])
    print("trying to compile submission")
    compiled = subprocess.call(docker_lst + [compiler, filename, "-lm", "-o", executable])
    if compiled != 0:
        print("submission didn't compile")
        submission.status = "CE"
        submission.save()
    else:
        print("submission compiled successfully")
        print("running the submission")
        user_output_filename = f"{submission_id}.output"
        options_lst = ["python3", "run.py", executable, input_filename, user_output_filename, str(time_limit)]
        print(docker_lst + options_lst)
        subprocess.call(["docker", "cp", "run.py", "{}:/run.py".format(container_id)])
        run_code = subprocess.check_output(docker_lst + options_lst)
        print(run_code)
        run_code = int(run_code.decode("utf-8"))
        if run_code == 124:
            # time limit exceeded
            print("time limit exceeded")
            submission.status = "TLE"
            submission.save()
        elif run_code != 0:
            # run time error
            print("run time error")
            submission.status = "RE"
            submission.save()
        else:
            print("code ran in time, now have to check with output")
            # will use diff for that, diff returns 0 if no differences, non zero if there are
            # differences or if something bad happens
            print('copying output')
            subprocess.call(["docker", "cp", "{}:/{}".format(container_id, user_output_filename), "outputs/{}".format(user_output_filename)])
    subprocess.call(["docker", "stop", container_id])

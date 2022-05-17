#!/usr/bin/python

import argparse
import rosbag
import rospy
import os
import zipfile
import shutil
import sys
from os.path import basename
import h5py
import numpy as np


# Function borrowed from: https://stackoverflow.com/a/3041990
def query_yes_no(question, default="yes"):
    """Ask a yes/no question via raw_input() and return their answer.

    "question" is a string that is presented to the user.
    "default" is the presumed answer if the user just hits <Enter>.
        It must be "yes" (the default), "no" or None (meaning
        an answer is required of the user).

    The "answer" return value is True for "yes" or False for "no".
    """
    valid = {"yes": True, "y": True, "ye": True,
             "no": False, "n": False}
    if default is None:
        prompt = " [y/n] "
    elif default == "yes":
        prompt = " [Y/n] "
    elif default == "no":
        prompt = " [y/N] "
    else:
        raise ValueError("invalid default answer: '%s'" % default)

    while True:
        sys.stdout.write(question + prompt)
        choice = raw_input().lower()
        if default is not None and choice == '':
            return valid[default]
        elif choice in valid:
            return valid[choice]
        else:
            sys.stdout.write("Please respond with 'yes' or 'no' "
                             "(or 'y' or 'n').\n")


def timestamp_str(ts):
    t = ts.secs + ts.nsecs / float(1e6) #1e9?
    return t
    #return '{:.12f}'.format(t)


if __name__ == "__main__":

    # arguments
    parser = argparse.ArgumentParser()
    parser.add_argument("bag", help="ROS bag file to extract")
    parser.add_argument("--output_folder", default="extracted_data", help="Folder where to extract the data")
    parser.add_argument("--event_topic", default="/dvs/events", help="Event topic")
    parser.add_argument('--no-zip', dest='no_zip', action='store_true')
    parser.set_defaults(no_zip=False)
    args = parser.parse_args()

    print('Data will be extracted in folder: {}'.format(args.output_folder))

    if not os.path.exists(args.output_folder):
        os.makedirs(args.output_folder)

    width, height = None, None
    event_sum = 0
    event_msg_sum = 0
    num_msgs_between_logs = 25
    output_name = os.path.basename(args.bag).split('.')[0]   # /path/to/mybag.bag -> mybag
    path_to_events_file = os.path.join(args.output_folder, '{}.hdf5'.format(output_name))

    #f = h5py.File(path_to_events_file, 'w')
    #f.close()
    #f = h5py.File('mydataset.hdf5', 'a')
    #grp = f.create_group("events")
    # dsetp = grp.create_dataset("p",  dtype='f')
    # dsetx = grp.create_dataset("x",  dtype='f')
    # dsety = grp.create_dataset("y",  dtype='f')
    # dsett = grp.create_dataset("t",  dtype='f')

    with h5py.File(path_to_events_file, 'w') as events_file:
        grp = events_file.create_group('events')

        with rosbag.Bag(args.bag, 'r') as bag:

            # Look for the topics that are available and save the total number of messages for each topic (useful for the progress bar)
            total_num_event_msgs = 0
            topics = bag.get_type_and_topic_info().topics
            #original:  for topic_name, topic_info in topics.iteritems():
            for topic_name, topic_info in topics.items():
                #print("topic_name"+topic_name+"\n")
                if topic_name == args.event_topic:
                    total_num_event_msgs = topic_info.message_count
                    print('Found events topic: {} with {} messages'.format(topic_name, topic_info.message_count))
                    dt = h5py.string_dtype(encoding='utf-8')


            plist = []
            xlist = []
            ylist = []
            tlist = []

            # Extract events to text file
            for topic, msg, t in bag.read_messages():
                #print("topic: "+topic + "\n") ####
                if topic == args.event_topic:
                    if width is None:
                        width = msg.width
                        height = msg.height
                        print('Found sensor size: {} x {}'.format(width, height))
                        #events_file.write("{} {}\n".format(width, height))

                    if event_msg_sum % num_msgs_between_logs == 0 or event_msg_sum >= total_num_event_msgs - 1:
                        print('Event messages: {} / {}'.format(event_msg_sum + 1, total_num_event_msgs))
                    event_msg_sum += 1

                    #if (event_msg_sum ==51) : break
                    for e in msg.events:
                        polarity = 1 if e.polarity else 0
                        plist.append(polarity)
                        xlist.append(e.x)
                        ylist.append(e.y)
                        tlist.append(timestamp_str(e.ts))
                        event_sum += 1
            #print(tlist)
            dsetp = grp.create_dataset("p", dtype = 'f', data = np.array(plist))
            dsetx = grp.create_dataset("x", dtype = 'f', data = np.array(xlist))
            dsety = grp.create_dataset("y", dtype = 'f', data = np.array(ylist))
            dsett = grp.create_dataset("t", dtype = 'f', data = np.array(tlist))
            #dsetp = np.array(plist)
                    #dsetx = grp.create_dataset("x", dtype=dt)
                    #dsety = grp.create_dataset("y",  dtype=dt)
                    #dsett = grp.create_dataset("t", dtype=dt)

                    #events_file['events/y'][event_sum] = str(e.y)
            #dsetx = np.array(xlist)
            #dsety = np.array(ylist)
            #dsett = np.array(tlist)

                    
        # statistics

        #with h5py.File(path_to_events_file, 'r') as f:
        #    print(f['events/x'][0])
        print('All events extracted!')
        print('Events:', event_sum)

    # Zip text file
    # if not args.no_zip:
    #     print('Compressing text file...')
    #     path_to_events_zipfile = os.path.join(args.output_folder, '{}.zip'.format(output_name))
    #     with zipfile.ZipFile(path_to_events_zipfile, 'w') as zip_file:
    #         zip_file.write(path_to_events_file, basename(path_to_events_file), compress_type=zipfile.ZIP_DEFLATED)
    #     print('Finished!')

    #     # Remove events.txt
    #     if query_yes_no('Remove text file {}?'.format(path_to_events_file)):
    #         if os.path.exists(path_to_events_file):
    #             os.remove(path_to_events_file)
    #             print('Removed {}.'.format(path_to_events_file))

    # print('Done extracting events!')

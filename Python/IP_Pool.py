#!/usr/bin/python
# -*- coding:UTF-8 -*-
#**********************************************	#
# Master and Slave Handshake Protocal 			#
# AutoPanic主从服务器通信协议	                #
#----------------------------------------------	#
# @Author: Cyril								#
# @Mail: 848873227@qq.com                       #
# @Create: 2019-06-08							#
# @Tips: 			                            #
#**********************************************	#

from jc import utils as jcu
import os
import re
import sys

class IP_Pool:
	ip_pool = []    # 二维数组
	conf_path = "/tmp/autopanic_ips_stats.csv"
	origin_data=[
		["Station", "IP", "Stats", "role"],
		["s1", "172.21.156.46", "Online", "master"],
		["s2", "172.21.204.237", "Online", "slave"],
		["s3", "172.21.204.238", "Online", "slave"],
		["s4", "172.21.204.239", "Online", "slave"],
	]

	def __init__(self, conf_path=conf_path, remotePool=False):
		self.sys_ver = sys.version
		self.ip_pool=jcu.readCSVFile(conf_path)
		if self.ip_pool and len(self.ip_pool) > 0:
			#print("Init failed. Make a new config-%s" %conf_path)
			#jcu.writeCSVFile(conf_path, self.origin_data)
			self.ip_pool.remove(self.ip_pool[0])

		if os.path.exists(conf_path) and remotePool:
			conf_parent_path = os.path.split()[0]
			pass


	def run_IP_Pool(self):
		pass

	def setIPStats(self, IP, Stats="Online"):
		"""
		# Add/Update IPStats to local IP_Pool
		# 请勿直接调用此方法
		:param IP:
		:param Stats: Online/Offline (str)
		:return: True/False
		"""
		print (self.ip_pool)

	def fullSync(self, remoteIP, syncFileOrDir, reverse=False, remoteUser="gdlocal", remotePWD="gdlocal"):
		"""
		# Full synchronization
		# 两个工站进行全量同步 （其中一个是本机）
		:param remoteIP: 远程工站IP需手动指定
		:param syncFileOrDir: 要同步的文件或文件夹
		:param reverse: 是否反向同步 True/False
						# False: 正向同步，覆盖远程文件
						# True: 反向同步，即下载远程文件到本地临时文件
		:param remoteUser: 被同步文件工站用户名
		:param remoteUser: 被同步文件工站用户密码
		:return: True/False
		"""
		if not re.match("\d+.\d+.\d+.\d+", remoteIP):
			print("'IP' is invalid type.")
			exit(1)

		(dir, filename) = os.path.split(syncFileOrDir)
		## -u 不同步旧版本
		if reverse:
			sync_cmd = "/usr/bin/rsync -avu %s@%s://%s %s" %( remoteUser, remoteIP, syncFileOrDir, dir)
		else:
			sync_cmd = "/usr/bin/rsync -avu %s %s@%s://%s" % (syncFileOrDir, remoteUser, remoteIP, dir)

		cmd = """
	expect << EOF
	set timeout 3
	spawn %s
	expect {
	        -re "Password:" { send "%s\r"; exp_continue }
	        -re "total size is" { exit 0}
	    timeout {
	        send_user "Timeout...exit.\r" ;
	        exit 1
	    }
	        eof {
	                send_user "EOF finish.\r" ;
	                exit 2
	        }
	}
	EOF
	        """ %(sync_cmd, remotePWD)
		#% (dir, filename, remoteIP, dir)
		(res, rev) = jcu.readCMD(cmd, True)
		#print("syncConfigOn2Stations (res, rev) -> %s" %str((res,rev)))
		if res == 0:
			return True
		return False

	def increSync(self, remoteIP, syncFileOrDir, reverse=False, remoteUser="gdlocal", remotePWD="gdlocal"):
		"""
		# Incremental synchronization
		# 两个工站进行增量同步 （其中一个是本机）
		# Tips: 适用于单文件单增量同步，传入单syncFileOrDir若是文件夹则可能失败
		:param remoteIP: 远程工站IP需手动指定
		:param syncFileOrDir: 要同步的文件或文件夹
		:param reverse: 是否反向同步 True/False
		:param remoteUser: 被同步文件工站用户名
		:param remoteUser: 被同步文件工站用户密码
		:return: True/False
		"""
		if not os.path.isfile(syncFileOrDir):
			print("'syncFileOrDir' should be a exist file path.")
			return False

		# 反向同步，即下载远程文件到本地
		if not self.fullSync(remoteIP, syncFileOrDir+".1", True, remoteUser, remotePWD):
			print("Get remote file failed. [IP:%s]" %remoteIP)
			return False

		remote_data = jcu.readCSVFile(syncFileOrDir+".1")
		local_data = jcu.readCSVFile(syncFileOrDir)
		## 将本地数据与远程数据对比合并重复项，并写入新数据
		if remote_data and local_data and remote_data == local_data:
			## 如果数据对比相同则不写入新数据和远程同步
			return True
		else:
			new_data = self.mergeLists(remote_data, local_data)
			# 清空原数据表
			with open(syncFileOrDir, "w") as f:
				f.write("")
			jcu.writeCSVFile(syncFileOrDir, new_data)
			if self.fullSync(remoteIP, syncFileOrDir, False, remoteUser, remotePWD):
				return True
		return False
		#remote_data =

	def mergeLists(self, *args):
		"""
		# 合并所有的list，自动去除相同项
		:param data_1:
		:param data_2:
		:return: merged list (set)
		"""
		if not args:
			return []
		merged_list = set()
		for item in args:
			for i_list in item:
				try:
					merged_list.add(tuple(i_list))
				except Exception as e:
					print("item-%s added failed." % str(i_list))
					print(e)
					continue

		return sorted(merged_list, key=lambda x: x[0], reverse=False)

def main():
	"""
	## Python的入口开始
	:return:
	"""
	module = sys.modules[__name__]
	# getattr() 函数用于返回一个对象属性值。
	# sys.argv 是获取运行python文件的时候命令行参数,且以list形式存储参数
	# sys.argv[0] 代表当前module的名字
	try:
		func = getattr(module, sys.argv[1])
	except Exception as e:
		print(e)
	else:
		args = None
		if len(sys.argv) > 1:
			args = sys.argv[2:]
			#print("DEBUG: args = %s" %args)
			func(*args)


if __name__ == "__main__":
	ipp = IP_Pool()
	#print (ipp.ip_pool)
	print("==>")
	#print (ipp.fullSync("172.21.204.238", "/tmp/autopanic_ips_stats.csv"))
	print(ipp.increSync("172.21.204.238", "/tmp/autopanic_ips_stats.csv", reverse=False, remoteUser="gdlocal", remotePWD="gdlocal"))
	pass



else:
	main()
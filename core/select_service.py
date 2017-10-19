from config.general_config import GENERAL_CONFIG
from logs import Log

import sys
import select

#
# Base class for a "selectible" object, which can read/write using the SelectService
# Selectibles should override on_read_ready and implement it to read from the fd
# Selectibles should use write_to_fd to write to the fd (never use plain .write!)
#
class Selectible(object):
	def initialize_selectible_fd(self, fd):
		self.pending_write_to_fd = bytearray([])
		self.fd = fd
		self.write_function = "write" if "write" in dir(fd) else "send" # some have .write, some have .send
		SelectService.register_selectible(self)

	def destroy_selectible(self):
		SelectService.deregister_selectible(self)

	def write_to_fd(self, data):
		self.pending_write_to_fd += data

	def on_read_ready(self, cur_time_s):
		pass

	def on_write_ready(self, cur_time_s):
		try:
			# call the write function
			getattr(self.fd, self.write_function)(self.pending_write_to_fd)
			self.pending_write_to_fd = bytearray([])
		except:
			Log.debug("Selectible::on_write_ready() failed.", exception=True)

#
# A simple select-based event pump
#
class SelectService(object):
	# a dictionary of selectible-string -> selectible
	selectibles = {}

	# Registers a selectible
	# selectible  A Selectible object
	@staticmethod
	def register_selectible(selectible):
		SelectService.selectibles[str(selectible)] = selectible

	# Deregisters a selectible
	@staticmethod
	def deregister_selectible(selectible):
		key = str(selectible)
		if key in SelectService.selectibles:
			del SelectService.selectibles[key]

	# Performs a select with a timeout to wait for selectibles to be ready for reading or writing
	# cur_time_s  Current time in seconds
	@staticmethod
	def perform_select(cur_time_s, select_reads=True, select_writes=True):
		all_selectibles = SelectService.selectibles.values()

		read_descriptors = []
		write_descriptors = []

		if select_reads:
			readable_descriptors = dict(map(lambda s: (str(s.fd), s), all_selectibles))
			read_descriptors = list(map(lambda rd: rd.fd, readable_descriptors.values()))

		if select_writes:
			writable_descriptors = dict(map(lambda s: (str(s.fd), s), filter(lambda s: len(s.pending_write_to_fd) > 0, all_selectibles)))
			write_descriptors = list(map(lambda wd: wd.fd, writable_descriptors.values()))

		if len(read_descriptors) + len(write_descriptors) == 0:
			return # nothing to select

		try:
			(ready_read_descriptors, ready_write_descriptors, _) = select.select(read_descriptors, write_descriptors, [], GENERAL_CONFIG.SELECT_TIMEOUT)
			for D in ready_write_descriptors:
				try:
					writable_descriptors[str(D)].on_write_ready(cur_time_s)
				except: pass
			for D in ready_read_descriptors:
				try:
					readable_descriptors[str(D)].on_read_ready(cur_time_s)
				except: pass
		except KeyboardInterrupt:
			raise
		except:
			Log.debug("Select failed.", exception=True)

